import argparse
import configparser
import os

from faca_calc import FacaCalc


class FacaMain:

    def __init__(self, iniFile=None, section=None, ui=False, args=None):
        if ui:
            self.startUi()
            return
        elif iniFile and section:
            settings = self.getSettingsFromIniSection(iniFile, section)
            settings = self.updateSettingsFromArgs(settings, args)
        elif self.checkArgsComplete(args):
            settings = self.updateSettingsFromArgs({}, args)
        else:
            settings = self.getSettingsFromInput(args)
        f = FacaCalc(**settings)
        f.main()

    def startUi(self) -> None:
        from faca_ui import FacaUi
        from tkinter import Tk

        root = Tk()
        fUi = FacaUi(root=root, calcClass=FacaCalc)
        fUi.mainloop()

    def getSettingsFromIniSection(self, iniFile: str, section: str) -> dict:
        settingsDict = {}
        settings = configparser.ConfigParser()
        settings.read(iniFile)
        settingsDict["project_name"] = settings[section]["project_name"]
        settingsDict["input_image_dir"] = settings[section]["input_image_dir"]
        settingsDict["output_dir"] = settings[section]["output_dir"]
        settingsDict["alignment_accuracy"] = settings[section].getint(
            "alignment_accuracy"
        )
        settingsDict["camera_accuracy"] = settings[section]["camera_accuracy"]
        settingsDict["keypoint_limit"] = settings[section].getint("keypoint_limit")
        settingsDict["tiepoint_limit"] = settings[section].getint("tiepoint_limit")
        settingsDict["criterions"] = settings[section]["criterions"]
        settingsDict["criterion_values"] = settings[section]["criterion_values"]
        settingsDict["depth_map_quality"] = settings[section].getint(
            "depth_map_quality"
        )
        settingsDict["depth_map_filtering"] = settings[section]["depth_map_filtering"]
        settingsDict["output_epsg_code"] = settings[section]["output_epsg_code"]
        return settingsDict

    def updateSettingsFromArgs(self, settings: dict, args: argparse.Namespace) -> dict:
        for attribute in vars(args):
            value = getattr(args, attribute)
            if value is not None:
                if attribute in [
                    "alignment_accuracy",
                    "keypoint_limit",
                    "tiepoint_limit",
                    "depth_map_quality",
                ]:
                    settings[attribute] = int(value)
                elif attribute in [
                    "input_image_dir",
                    "output_dir",
                    "output_epsg_code",
                    "project_name",
                    "camera_accuracy",
                    "criterions",
                    "criterion_values",
                ]:
                    settings[attribute] = value
        return settings

    def checkArgsComplete(self, args: argparse.Namespace) -> bool:
        if None in [
            args.input_image_dir,
            args.output_dir,
            args.output_epsg_code,
            args.project_name,
            args.alignment_accuracy,
            args.camera_accuracy,
            args.keypoint_limit,
            args.tiepoint_limit,
            args.criterions,
            args.criterion_values,
            args.depth_map_quality,
            args.depth_map_filtering,
        ]:
            return False
        return True

    def getSettingsFromInput(self, args) -> dict:
        settings = self.updateSettingsFromArgs({}, args)
        if settings:
            print("Settings provided by command line arguments:")
            for k, v in settings.items():
                print(f"{k}: {v}")

        def p(prompt: str, default: str, explanation: str):
            # prompt for value
            print(f"{explanation}")
            return input(f"{prompt} [{default}]: ") or default

        if "project_name" not in settings:
            settings["project_name"] = p(
                "Project name",
                "faca.psx",
                "This is the name of the project file (ending with '.psx').",
            )
        if "input_image_dir" not in settings:
            settings["input_image_dir"] = p(
                "Input images directory",
                "images",
                "The directory containing input images. Each survey in its own subdirectory.",
            )
        if "output_dir" not in settings:
            settings["output_dir"] = p(
                "Output directory",
                "out",
                "Directory where all output files will be saved.",
            )
        if "alignment_accuracy" not in settings:
            settings["alignment_accuracy"] = int(
                p(
                    "Image alignment accuracy",
                    "1",
                    "0 - Highest, 1 - High, 2 - Medium, 4 - Low, 8 - Lowest.",
                )
            )
        if "camera_accuracy" not in settings:
            settings["camera_accuracy"] = p(
                "Camera Accuracy",
                "None",
                "In meters (',' to separate XYZ) or from EXIF ('EXIF') or Default (= 10 m) ('None')",
            )
        if "keypoint_limit" not in settings:
            settings["keypoint_limit"] = int(
                p(
                    "Key Point Limit",
                    "40000",
                    "The maximum number of feature points used as key points per image.",
                )
            )
        if "tiepoint_limit" not in settings:
            settings["tiepoint_limit"] = int(
                p(
                    "Tie Point Limit",
                    "4000",
                    "The maximum number of matching points used as tie points per image.",
                )
            )
        if "criterions" not in settings:
            settings["criterions"] = p(
                "Tie Point Filter Criterions (',' to separate)",
                "ImageCount,ReconstructionUncertainty,ProjectionAccuracy",
                "Any combination of ImageCount, ProjectionAccuracy, ReconstructionUncertainty, ReprojectionError or 'None' to disable filtering.",
            )
        if "criterion_values" not in settings:
            settings["criterion_values"] = p(
                "Tie Point Filter Criterion Values (',' to separate)",
                "3,50,10",
                "Threshold values for the filtering criterions, corresponding to each criterion in the order provided.",
            )
        if "depth_map_quality" not in settings:
            settings["depth_map_quality"] = int(
                p(
                    "Depth Map Quality",
                    "4",
                    "1 - Ultra high, 2 - High, 4 - Medium, 8 - Low, 16 - Lowest.",
                )
            )
        if "depth_map_filtering" not in settings:
            settings["depth_map_filtering"] = p(
                "Depth Map Filter Mode",
                "AggressiveFiltering",
                "Select filtering mode: NoFiltering, MildFiltering, ModerateFiltering, AggressiveFiltering.",
            )
        if "output_epsg_code" not in settings:
            settings["output_epsg_code"] = p(
                "Output EPSG",
                "32632",
                "EPSG code for the output coordinate system (e.g., 32632 for WGS 84 / UTM zone 32N).",
            )
        return settings


if __name__ == "__main__":
    working_directory = os.path.dirname(os.path.realpath(__file__))
    os.chdir(working_directory)
    file = os.path.basename(__file__)

    parser = argparse.ArgumentParser(
        prog="FACA",
        description=f"""Fully Automated Co-Alignment
        Usage examples:

        '{file} --iniFile faca.ini --Section \"FACA defaults\"' starts calculation with values from .ini Section
        '{file} --ui' starts the FACA Userinterface
        '{file}' starts FACA in user input mode.
        '{file} --iniFile faca.ini --Section \"FACA defaults\" --input_image_dir new_dir' starts calculation with values from .ini Section but replaces the input_image_dir parameter.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
There are three ways FACA handles indivual parameters defined on the command line:
    1. If not all parameters are given but a configuration file and section, the parameters replace corresponding values, and the calculation starts.
    2. If all parameters, but neither a configuration file nor section are given, the calculation starts.
    3. If not all parameters are given, and neither a configuration file nor a section, the interactive mode starts, skipping defined parameters.""",
    )
    parser.add_argument("-i", "--iniFile", help="Path to the ini file.", required=False)
    parser.add_argument(
        "-s", "--Section", help="Section in the ini file.", required=False
    )
    parser.add_argument(
        "-u", "--ui", action="store_true", help="Launch the GUI.", required=False
    )
    parser.add_argument(
        "--input_image_dir",
        help="Path to input images, with each survey in a separate subdirectory.",
        required=False,
    )
    parser.add_argument(
        "--output_dir",
        help="Path to the output directory.",
        required=False,
    )
    parser.add_argument(
        "--output_epsg_code",
        help="Digits of the the ouput EPSG code.",
        required=False,
    )
    parser.add_argument(
        "--project_name",
        help="Project name for saving, with a '.psx' extension..",
        required=False,
    )
    parser.add_argument(
        "--alignment_accuracy",
        help="Image alignment accuracy; options: 0 - Highest, 1 - High, 2 - Medium, 4 - Low, 8 - Lowest.",
        required=False,
    )
    parser.add_argument(
        "--camera_accuracy",
        help="Camera accuracy XYZ in meters (use ',' to separate) or from EXIF ('EXIF') or default ('None').",
        required=False,
    )
    parser.add_argument(
        "--keypoint_limit",
        help="Maximum number of feature points to use as key points per image.",
        required=False,
    )
    parser.add_argument(
        "--tiepoint_limit",
        help="Maximum number of matching points to use as tie points per image.",
        required=False,
    )
    parser.add_argument(
        "--criterions",
        help="""Any combination of ImageCount, ProjectionAccuracy, ReconstructionUncertainty, 
        ReprojectionError, or 'None' to disable filtering.""",
        required=False,
    )
    parser.add_argument(
        "--criterion_values",
        help="""Sets the thresholds for the filtering criteria, with each value corresponding
        to its respective criterion in order.""",
        required=False,
    )
    parser.add_argument(
        "--depth_map_quality",
        help="Depth Map Quality; options: 1 - Ultra high, 2 - High, 4 - Medium, 8 - Low, 16 - Lowest.",
        required=False,
    )
    parser.add_argument(
        "--depth_map_filtering",
        help="Depth Map Filter Mode; options: NoFiltering, MildFiltering, ModerateFiltering, AggressiveFiltering.",
        required=False,
    )
    args = parser.parse_args()

    if args.ui:
        FacaMain(ui=True)
    elif args.iniFile and args.Section:
        FacaMain(iniFile=args.iniFile, section=args.Section, args=args)
    else:
        FacaMain(args=args)
