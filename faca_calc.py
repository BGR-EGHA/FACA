import glob

import Metashape
import os

from faca_log import Logger


class FacaCalc:
    """
    Class to handle FACA co-alignment calculations.

    Attributes:
        l (Logger): Logger instance for logging the process and results.
        projectName (str): Name of the project.
        inputImageDir (str): Directory path for input images.
        outputDir (str): Directory path for output files.
        alignmentAccuracy (int): Accuracy setting for image alignment (lower is more detailed).
        cameraAccuracy (str or None): Camera accuracy setting (can be "None" or x,y,z or "EXIF").
        keypointLimit (int): Maximum number of keypoints per image.
        tiepointLimit (int): Maximum number of tiepoints per image.
        criterionsDict (dict): Dictionary of filtering criterions and their corresponding values.
        depthMapQuality (int): Quality level of the depth map (lower is more detailed).
        depthMapFiltering (str): Filter mode for the depth map.
        outputEpsg (int): EPSG code for the coordinate system of the output files.
    """

    def __init__(self, **kwargs):
        self.l = Logger()
        self.l.setupLogger(kwargs["output_dir"], kwargs["project_name"])
        self.l.l("FACA Log")
        self.l.l(f"Metashape Version: {Metashape.version}")
        self.l.l("Parameters:")
        self.l.logFacaInputs(kwargs)

        self.projectName = kwargs["project_name"]  # str
        self.inputImageDir = kwargs["input_image_dir"]  # str
        self.outputDir = kwargs["output_dir"]  # str
        self.alignmentAccuracy = kwargs["alignment_accuracy"]  # int
        self.cameraAccuracy = kwargs["camera_accuracy"]  # str
        if self.cameraAccuracy == "None":
            self.cameraAccuracy = None
        self.keypointLimit = kwargs["keypoint_limit"]  # int
        self.tiepointLimit = kwargs["tiepoint_limit"]  # int
        criterions = [
            c.strip() for c in kwargs["criterions"].split(",")
        ]  # list of strs
        criterionValues = list(  # list of floats
            map(float, [c.strip() for c in kwargs["criterion_values"].split(",")])
        )
        self.criterionsDict = dict(zip(criterions, criterionValues))
        self.depthMapQuality = int(kwargs["depth_map_quality"])  # int
        self.depthMapFiltering = kwargs["depth_map_filtering"]  # str
        self.outputEpsg = int(kwargs["output_epsg_code"])  # int

    def _validate(self) -> bool:
        """
        Validate the inputs.
        """
        ok = True
        okAlignmentAccuracy = (0, 1, 2, 4, 8)
        okCriterion = (
            "ImageCount",
            "ProjectionAccuracy",
            "ReconstructionUncertainty",
            "ReprojectionError",
            "None",
        )
        okDepthMapQuality = (1, 2, 4, 8, 16)
        okDepthMapFiltering = (
            "NoFiltering",
            "MildFiltering",
            "ModerateFiltering",
            "AggressiveFiltering",
        )
        if not self.alignmentAccuracy in okAlignmentAccuracy:
            self.l.lwt(
                f"Invalid image alignment accuracy: {self.alignmentAccuracy}. {okAlignmentAccuracy = }"
            )
            ok = False
        for criterion in self.criterionsDict:
            if not criterion in okCriterion:
                self.l.lwt(
                    f"Invalid tie point filtering criterion: {criterion}. {okCriterion = }"
                )
                ok = False
        if not self.depthMapQuality in okDepthMapQuality:
            self.l.lwt(
                f"Invalid depth map quality: {self.depthMapQuality}. {okDepthMapQuality = }"
            )
            ok = False
        if not self.depthMapFiltering in okDepthMapFiltering:
            self.l.lwt(
                f"Invalid depth map filtering: {self.depthMapFiltering}. {okDepthMapFiltering = }"
            )
            ok = False
        return ok

    def main(self) -> None:
        """
        Main FACA execution method.

        Steps:
            1.  Validates input parameters.
            2.  Get survey count and names.
            3.  Get individual survey images.
            4.  Initialize a Metashape project and add an "Original" chunk.
            5.  Load all images into "orignal" chunk.
            6.  Set Image Accuracy.
            7.  Align and match the images to generate tie points.
            8.  Optimize the sparse point cloud by filtering bad points and realigning.
            9.  Clone chunks and remove irrelevant camera groups.
            10. Build dense point clouds for each chunk.
            11. Export the point clouds.
        """
        self.l.lwt("start.")
        if not self._validate():
            self.l.lwt("Input Parameter Validation failed.")
            return
        self.l.lwt("Input Parameter Validation finished sucessfully.")

        chunkNames = self.getChunkNames(self.inputImageDir)
        self.l.lwt(f"Found {len(chunkNames)} directories: {chunkNames}")
        imagesDict = self.getImagesByChunkName(self.inputImageDir, chunkNames)
        self.l.logImagesDict(imagesDict)

        doc = Metashape.Document()
        doc.save(os.path.join(self.outputDir, self.projectName))
        origChunk = self.addLabeledChunk(doc, "Original")
        self.l.lwt("Original chunk added.")
        doc.save()

        self.addImagesByChunkName(origChunk, imagesDict)
        self.l.lwt(f"{len(origChunk.cameras)} images added to {origChunk.label}.")
        doc.save()

        self.setImageAccuracy(origChunk)
        self.l.lwt(f"Image Accuracy set to {self.cameraAccuracy}.")
        doc.save()

        self.matchAndAlign(origChunk)
        self.l.lwt(f"{origChunk.label} matched and aligned.")
        self.l.l(
            f"{origChunk.label} Tie Point Count: {len(origChunk.tie_points.points)}"
        )
        doc.save()

        self.removeBadPointsAndRealign(origChunk)  # logging in function
        doc.save()

        newChunks = self.CloneChunkNewLabels(origChunk, chunkNames)
        self.l.lwt(f"New Chunks created: {chunkNames}")
        self.removeCameraGroupsUnequalChunkName(newChunks)
        self.l.lwt(f"Removed images from other surveys.")
        self.l.logNewChunkInfos(newChunks)
        doc.save()

        self.buildPointClouds(newChunks)  # logging in function
        doc.save()

        self.exportPointClouds(newChunks)  # logging in function
        doc.save()
        self.l.lwt("done.")

    def addLabeledChunk(
        self, doc: Metashape.Metashape.Document, label: str
    ) -> Metashape.Metashape.Chunk:
        chunk = doc.addChunk()
        chunk.label = label
        return chunk

    def addLabeledCameraGroup(
        self, chunk: Metashape.Metashape.Chunk, label: str
    ) -> Metashape.Metashape.CameraGroup:
        cg = chunk.addCameraGroup()
        cg.label = label
        return cg

    def CloneChunkNewLabels(
        self, inChunk, newLabels: list[str]
    ) -> list[Metashape.Chunk]:
        newChunks = []
        for label in newLabels:
            newChunk = inChunk.copy()
            newChunk.label = label
            newChunks.append(newChunk)
        return newChunks

    def getImagesByChunkName(
        self, folder: str, chunkNames: list[str]
    ) -> dict[str, list[str]]:
        """
        Retrieves images recursivly for each subdirectory (chunkNames) in folder.
        Returns a dictionary where keys are chunkNames and values are lists of their image file paths.
        """
        imagesDict = {}
        for c in chunkNames:
            chunkPath = os.path.join(folder, c)
            chunkImageList = glob.glob(
                chunkPath + f"{os.path.sep}**{os.path.sep}*.JPG", recursive=True
            )
            imagesDict[c] = chunkImageList
        return imagesDict

    def getCameraGroupByLabel(
        chunk: Metashape.Metashape.Chunk, label: str
    ) -> Metashape.Metashape.CameraGroup:
        # unused
        for cg in chunk.camera_groups:
            if cg.label == label:
                return cg
        return None

    def getChunkNames(self, folder: str) -> list[str]:
        """
        Returns the names of subdirectories within folder.
        Expects folder to contain at least two subdirectories, as each subdirectory represents a survey.
        """
        chunkNames = [os.path.basename(f) for f in os.scandir(folder) if f.is_dir()]
        if len(chunkNames) < 2:
            raise ValueError(
                f"Expected >= 2 subfolders in Image Directory. Found {len(chunkNames)}: {chunkNames}"
            )
        return chunkNames

    def addImagesByChunkName(
        self, chunk: Metashape.Metashape.Chunk, imagesDict: dict[str, list[str]]
    ) -> None:
        """
        Adds images (imagesDict values) to chunk
        and organizes them into camera groups based on chunknames (imagesDict keys).
        Loads accuracy information from xmp metadata if self.cameraAccuracy == "EXIF".
        """
        if self.cameraAccuracy == "EXIF":
            loadXmpAccuracy = True
        else:
            loadXmpAccuracy = False
        for chunkName, images in imagesDict.items():
            cameraGroup = self.addLabeledCameraGroup(chunk, chunkName)
            chunk.addPhotos(images, load_xmp_accuracy=loadXmpAccuracy)
            for camera in chunk.cameras:
                if not camera.group:
                    camera.group = cameraGroup

    def setImageAccuracy(self, chunk: Metashape.Metashape.Chunk) -> None:
        """
        Sets the camera location accuracy to a custom value if one is defined.
        """
        if self.cameraAccuracy is None or self.cameraAccuracy == "EXIF":
            return
        accuracyVector = self._getAccuracyFromString()
        for camera in chunk.cameras:
            camera.reference.accuracy = accuracyVector

    def _getAccuracyFromString(self) -> Metashape.Vector:
        return Metashape.Vector(list(map(float, self.cameraAccuracy.split(","))))

    def matchAndAlign(self, chunk: Metashape.Metashape.Chunk) -> None:
        chunk.matchPhotos(
            downscale=self.alignmentAccuracy,
            keypoint_limit=self.keypointLimit,
            tiepoint_limit=self.tiepointLimit,
        )
        chunk.alignCameras()

    def removeBadPointsAndRealign(self, chunk: Metashape.Metashape.Chunk) -> None:
        for criterionStr, criterionValue in self.criterionsDict.items():
            criterion = self._getCriterionFromString(criterionStr)
            if criterion:  # do nothing is criterion is None
                filter = Metashape.TiePoints.Filter()
                filter.init(chunk, criterion)
                filter.removePoints(criterionValue)
                chunk.alignCameras(adaptive_fitting=True, reset_alignment=False)
                self.l.lwt(
                    f"{chunk.label} Tie Point Count after filtering with {criterionStr} and {criterionValue}: {len(chunk.tie_points.points)}"
                )

    def _getCriterionFromString(self, string: str):
        if string == "ImageCount":
            return Metashape.TiePoints.Filter.ImageCount
        elif string == "ProjectionAccuracy":
            return Metashape.TiePoints.Filter.ProjectionAccuracy
        elif string == "ReconstructionUncertainty":
            return Metashape.TiePoints.Filter.ReconstructionUncertainty
        elif string == "ReprojectionError":
            return Metashape.TiePoints.Filter.ReprojectionError
        elif string == "None":
            return None
        raise ValueError(f"No Criterion for String '{string}' found.")

    def removeCameraGroupsUnequalChunkName(
        self, chunks: list[Metashape.Metashape.Chunk]
    ) -> None:
        for chunk in chunks:
            for camera in chunk.cameras:
                if camera.group.label != chunk.label:
                    chunk.remove(camera.group)

    def buildPointClouds(self, chunks: list[Metashape.Metashape.Chunk]) -> None:
        """
        First generates depth maps from depth map filter mode and quality and then dense PCs.
        """
        filterMode = self._getFilterModeFromString(self.depthMapFiltering)
        for chunk in chunks:
            # downscale: (1 - Ultra high, 2 - High, 4 - Medium, 8 - Low, 16 - Lowest)
            chunk.buildDepthMaps(
                downscale=self.depthMapQuality,
                filter_mode=filterMode,
            )
            self.l.lwt(f"{chunk.label} Depth Map build with {self.depthMapFiltering}.")
            chunk.buildPointCloud()
            densePointsStr = str(chunk.point_cloud).split("'")[1].split(" ")[0]
            self.l.lwt(
                f"{chunk.label} Point Cloud build. Point Count: {densePointsStr}"
            )

    def _getFilterModeFromString(self, string: str):
        if string == "NoFiltering":
            return Metashape.NoFiltering
        elif string == "MildFiltering":
            return Metashape.MildFiltering
        elif string == "ModerateFiltering":
            return Metashape.ModerateFiltering
        elif string == "AggressiveFiltering":
            return Metashape.AggressiveFiltering
        raise ValueError(f"No Filter Mode for String '{string}' found.")

    def exportPointClouds(self, chunks: list) -> None:
        """
        Exports the dense clouds of each chunk in chunks as las files into the ouput directory.
        """
        for chunk in chunks:
            outputPath = os.path.join(self.outputDir, chunk.label + ".las")
            if self.outputEpsg:
                outputCrs = Metashape.CoordinateSystem("EPSG::" + str(self.outputEpsg))
                chunk.exportPointCloud(outputPath, crs=outputCrs)
            else:
                chunk.exportPointCloud(outputPath)
            self.l.lwt(
                f"Exported {chunk.label} Point Cloud with EPSG: {self.outputEpsg} to: {outputPath}"
            )
