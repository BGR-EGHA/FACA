from datetime import datetime
import logging
import os


class Logger:
    def setupLogger(self, outFolder, projectName):
        """Creates a .log text file in the output folder to log to."""
        logPath = os.path.join(outFolder, projectName + ".log")
        open(logPath, "w").close()  # replace if exists
        logging.basicConfig(
            filename=logPath,
            filemode="a",
            format="%(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG,
        )
        self.logger = logging.getLogger("faca")

    def l(self, message: str) -> None:
        self.logger.info(f"{message}")

    def lwt(self, message: str) -> None:
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logger.info(f"{time} - {message}")

    def logFacaInputs(self, inputDictionary) -> None:
        self.l(f"Project name:            {inputDictionary['project_name']}")
        self.l(f"Input Image Directory:   {inputDictionary['input_image_dir']}")
        self.l(f"Output Image Directory:  {inputDictionary['output_dir']}")
        self.l(f"Alignment Accuracy:      {inputDictionary['alignment_accuracy']}")
        self.l(f"Camera Accuracy:         {inputDictionary['camera_accuracy']}")
        self.l(f"Keypoint Limit:          {inputDictionary['keypoint_limit']}")
        self.l(f"Tiepoint Limit:          {inputDictionary['tiepoint_limit']}")
        self.l(f"Filter Criterions:       {inputDictionary['criterions']}")
        self.l(f"Filter Criterion Values: {inputDictionary['criterion_values']}")
        self.l(f"Depth Map Quality:       {inputDictionary['depth_map_quality']}")
        self.l(f"Depth Map Filtering:     {inputDictionary['depth_map_filtering']}")
        self.l(f"Output EPSG Code:        {inputDictionary['output_epsg_code']}")
        self.l("")

    def logImagesDict(self, imagesDict: dict) -> None:
        for directory, images in imagesDict.items():
            self.l(f"Images in {directory}: {len(images)}")

    def logNewChunkInfos(self, chunks) -> None:
        for c in chunks:
            self.l(
                f"{c.label} Image Count: {len(c.cameras)} Tie Point Count: {len(c.tie_points.points)}"
            )


if __name__ == "__main__":
    l = Logger()
    l.setupLogger("out", "test.psx")
    input_dir = {
        "project_name": "test",
        "input_image_dir": "input_folder",
        "output_dir": "output_folder",
        "alignment_accuracy": 1,
        "camera_accuracy": None,
        "keypoint_limit": 40_000,
        "tiepoint_limit": 4_000,
        "criterions": "ReconstructionUncertainty",
        "criterion_values": "50",
        "depth_map_quality": 4,
        "depth_map_filtering": "AggressiveFiltering",
        "output_epsg_code": 666,
    }
    l.logFacaInputs(input_dir)
    logging.info("test")
