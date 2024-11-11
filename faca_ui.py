import configparser
from idlelib.tooltip import Hovertip
import multiprocessing
import os
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *

from faca_calc import FacaCalc


class FacaUi(Frame):
    def __init__(self, root, calcClass):
        super().__init__(root)
        self.root = root
        self.init_ui()
        self.facacalc = calcClass
        if os.path.isfile("faca.ini"):
            self.ini_file = os.path.abspath("faca.ini")
            self._replace_entry(self.ini_path_entry, self.ini_file)
            # TODO: Update Ui when new .ini selected.
            self.update_ini_section_combobox()
            self.update_ui_with_ini_section("init")

    def init_ui(self):
        self.root.title("FACA - Fully Automated Co-Alignment")
        if os.path.isfile("faca.ico"):
            self.root.iconbitmap("faca.ico")
        self.root.resizable(False, False)

        self.ini_path_label = Label(self.root, text="Path to FACA .ini:")
        self.ini_path_label.grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.ini_path_entry = Entry(self.root, width=80)
        self.ini_path_tooltip = Hovertip(
            self.ini_path_entry,
            "Absolute or relative paths possible.",
        )
        self.ini_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        self.ini_path_button = Button(
            self.root, text="...", width=2, command=self.on_ini_path_button_clicked
        )
        self.ini_path_button.grid(row=0, column=2, padx=5, pady=5, sticky=W)

        self.ini_section_label = Label(self.root, text="Section in .ini:")
        self.ini_section_label.grid(row=0, column=3, padx=5, pady=5, sticky=W)
        self.ini_section_combobox = Combobox(
            self.root, state="readonly", text="Select a Section"
        )
        self.ini_section_combobox.bind(
            "<<ComboboxSelected>>", self.update_ui_with_ini_section
        )
        self.ini_section_combobox.grid(row=0, column=4, padx=5, pady=5, sticky=W)

        self.project_name_label = Label(self.root, text="Name of Metashape project:")
        self.project_name_label.grid(row=1, column=0, padx=5, pady=5, sticky=W)
        self.project_name_entry = Entry(self.root, width=80)
        self.project_name_tooltip = Hovertip(
            self.project_name_entry,
            "Must end with a '.psx' suffix.",
        )
        self.project_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)

        self.in_path_label = Label(self.root, text="Input Image Directory:")
        self.in_path_label.grid(row=2, column=0, padx=5, pady=5, sticky=W)
        self.in_path_entry = Entry(self.root, width=80)
        self.in_path_tooltip = Hovertip(
            self.in_path_entry,
            "Absolute or relative paths possible.",
        )
        self.in_path_entry.bind("<KeyRelease>", self.on_in_path_entry_changed)
        self.in_path_entry.grid(row=2, column=1, padx=5, pady=5, sticky=W)
        self.in_path_button = Button(
            self.root, text="...", width=2, command=self.on_in_path_button_clicked
        )
        self.in_path_button.grid(row=2, column=2, padx=5, pady=5, sticky=W)
        self.in_path_info_label = Label(
            self.root,
            text="To show image counts please select an input directory first.",
        )
        self.in_path_info_label.grid(
            row=2, column=3, padx=5, pady=5, columnspan=3, sticky=W
        )

        self.out_path_label = Label(self.root, text="Output Directory:")
        self.out_path_label.grid(row=3, column=0, padx=5, pady=5, sticky=W)
        self.out_path_entry = Entry(self.root, width=80)
        self.out_path_tooltip = Hovertip(
            self.out_path_entry,
            "Absolute or relative paths possible.",
        )
        self.out_path_entry.grid(row=3, column=1, padx=5, pady=5, sticky=W)
        self.out_path_button = Button(
            self.root, text="...", width=2, command=self.on_out_path_button_clicked
        )
        self.out_path_button.grid(row=3, column=2, padx=5, pady=5, sticky=W)

        self.alignment_accuracy_label = Label(
            self.root, text="Image Alignment Accuracy:"
        )
        self.alignment_accuracy_label.grid(row=4, column=0, padx=5, pady=5, sticky=W)
        self.alignment_accuracy_combobox = Combobox(
            self.root,
            state="readonly",
            values=["0 - Highest", "1 - High", "2 - Medium", "4 - Low", "8 - Lowest"],
        )
        self.alignment_accuracy_tooltip = Hovertip(
            self.alignment_accuracy_combobox,
            "Controls the level of image scaling applied during camera position estimation.",
        )
        self.alignment_accuracy_combobox.current(0)
        self.alignment_accuracy_combobox.grid(row=4, column=1, padx=5, pady=5, sticky=W)

        self.camera_accuracy_label = Label(self.root, text="Camera Location Accuracy:")
        self.camera_accuracy_label.grid(row=4, column=3, padx=5, pady=5, sticky=W)
        self.camera_accuracy_combobox = Combobox(
            self.root,
            state="readonly",
            values=["Default (10 m)", "Use Exif", "Custom"],
            validate="all",
            validatecommand=(
                self.register(self.on_camera_accuracy_combobox_changed),
                "%P",
            ),
        )
        self.camera_accuracy_combobox.current(0)
        self.camera_accuracy_tooltip = Hovertip(
            self.camera_accuracy_combobox,
            "Defines the expected positional accuracy in meters of each cameras coordinates.\nUse ',' to separate XYZ in Custom mode.",
        )
        self.camera_accuracy_combobox.grid(row=4, column=4, padx=5, pady=5, sticky=W)
        self.camera_accuracy_entry = Entry(
            self.root,
            state="disabled",
            validate="all",
            validatecommand=(self.register(self._val_only_int_comma), "%P"),
        )
        self.camera_accuracy_entry.grid(row=4, column=5, padx=5, pady=5, sticky=W)

        self.keypoint_limit_label = Label(self.root, text="Keypoint Limit:")
        self.keypoint_limit_label.grid(row=5, column=0, padx=5, pady=5, sticky=W)
        self.keypoint_limit_entry = Entry(
            self.root,
            validate="all",
            validatecommand=(self.register(self._val_only_int), "%P"),
        )
        self.keypoint_limit_tooltip = Hovertip(
            self.keypoint_limit_entry,
            "Max. feature points in an image.\nUse '0' for unlimited keypoints.",
        )
        self.keypoint_limit_entry.grid(row=5, column=1, padx=5, pady=5, sticky=W)

        self.tiepoint_limit_label = Label(self.root, text="Tiepoint Limit:")
        self.tiepoint_limit_label.grid(row=5, column=3, padx=5, pady=5, sticky=W)
        self.tiepoint_limit_entry = Entry(
            self.root,
            validate="all",
            validatecommand=(self.register(self._val_only_int), "%P"),
        )
        self.tiepoint_limit_tooltip = Hovertip(
            self.tiepoint_limit_entry,
            "Max. matching points in an image.\nUse '0' for unlimited tiepoints.",
        )
        self.tiepoint_limit_entry.grid(row=5, column=4, padx=5, pady=5, sticky=W)

        self.criterion_label_frame = LabelFrame(
            self.root, text="Tie Point Filter Criterions and Values"
        )
        self.criterion_label_frame.grid(
            row=6, column=0, padx=5, pady=5, columnspan=3, sticky=W
        )
        self.image_count_checkbutton = Checkbutton(
            self.criterion_label_frame,
            text="Use Image Count Criterion",
            onvalue=1,
            offvalue=0,
            command=self.on_filter_criterions_checkbuttons_toggled,
        )
        self.image_count_checkbutton.state(["!alternate"])
        self.image_count_checkbutton.grid(row=0, column=0, padx=5, pady=5, sticky=W)
        self.image_count_entry = Entry(
            self.criterion_label_frame,
            state="disabled",
            validate="all",
            validatecommand=(self.register(self._val_only_int), "%P"),
        )
        self.image_count_tooltip = Hovertip(
            self.image_count_entry,
            "Filters tiepoints based on the amount of images they are visible in.",
        )
        self.image_count_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)

        self.projection_accuracy_checkbutton = Checkbutton(
            self.criterion_label_frame,
            text="Use Projection Accuracy Criterion",
            onvalue=1,
            offvalue=0,
            command=self.on_filter_criterions_checkbuttons_toggled,
        )
        self.projection_accuracy_checkbutton.state(["!alternate"])
        self.projection_accuracy_checkbutton.grid(
            row=1, column=0, padx=5, pady=5, sticky=W
        )
        self.projection_accuracy_entry = Entry(
            self.criterion_label_frame,
            state="disabled",
            validate="all",
            validatecommand=(self.register(self._val_only_float), "%P"),
        )
        self.projection_accuracy_tooltip = Hovertip(
            self.projection_accuracy_entry,
            "Filters tiepoints based on the average image scale used when getting the tiepoint projection coordinates divided by the number of images containing the tiepoint.",
        )
        self.projection_accuracy_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)

        self.reconstruction_uncertainty_checkbutton = Checkbutton(
            self.criterion_label_frame,
            text="Use Reconstruction Uncertainty Criterion",
            onvalue=1,
            offvalue=0,
            command=self.on_filter_criterions_checkbuttons_toggled,
        )
        self.reconstruction_uncertainty_checkbutton.state(["!alternate"])
        self.reconstruction_uncertainty_checkbutton.grid(
            row=2, column=0, padx=5, pady=5, sticky=W
        )
        self.reconstruction_uncertainty_entry = Entry(
            self.criterion_label_frame,
            state="disabled",
            validate="all",
            validatecommand=(self.register(self._val_only_float), "%P"),
        )
        self.reconstruction_uncertainty_tooltip = Hovertip(
            self.reconstruction_uncertainty_entry,
            "Filters tiepoints based on  the ratio of the largest to the smallest semi-axis of the error ellipse of tiepoints.",
        )
        self.reconstruction_uncertainty_entry.grid(
            row=2, column=1, padx=5, pady=5, sticky=W
        )

        self.reprojection_error_checkbutton = Checkbutton(
            self.criterion_label_frame,
            text="Use Reprojection Error Criterion",
            onvalue=1,
            offvalue=0,
            command=self.on_filter_criterions_checkbuttons_toggled,
        )
        self.reprojection_error_checkbutton.state(["!alternate"])
        self.reprojection_error_checkbutton.grid(
            row=3, column=0, padx=5, pady=5, sticky=W
        )
        self.reprojection_error_entry = Entry(
            self.criterion_label_frame,
            state="disabled",
            validate="all",
            validatecommand=(self.register(self._val_only_float), "%P"),
        )
        self.reprojection_error_tooltip = Hovertip(
            self.reprojection_error_entry,
            "Filters tiepoints based on the maximum difference between measured and parameter adjusted coordinates of a tiepoint, normalized by the scale used.",
        )
        self.reprojection_error_entry.grid(row=3, column=1, padx=5, pady=5, sticky=W)

        self.depth_map_quality_label = Label(self.root, text="Depth Map Quality:")
        self.depth_map_quality_label.grid(row=7, column=0, padx=5, pady=5, sticky=W)
        self.depth_map_quality_combobox = Combobox(
            self.root,
            state="readonly",
            values=[
                "1 - Ultra high",
                "2 - High",
                "4 - Medium",
                "8 - Low",
                "16 - Lowest",
            ],
        )
        self.depth_map_quality_combobox.current(0)
        self.depth_map_quality_tooltip = Hovertip(
            self.depth_map_quality_combobox,
            "Defines the image resolution used when creating the depth map, and thus the detail and accuracy of the output geometry.",
        )
        self.depth_map_quality_combobox.grid(row=7, column=1, padx=5, pady=5, sticky=W)

        self.depth_map_filtering_label = Label(self.root, text="Depth Map Filtering:")
        self.depth_map_filtering_label.grid(row=7, column=3, padx=5, pady=5, sticky=W)
        self.depth_map_filtering_combobox = Combobox(
            self.root,
            state="readonly",
            values=[
                "No Filtering",
                "Mild Filtering",
                "Moderate Filtering",
                "Aggressive Filtering",
            ],
        )
        self.depth_map_filtering_combobox.current(0)
        self.depth_map_filtering_tooltip = Hovertip(
            self.depth_map_filtering_combobox,
            "Removes outliers from the depth map.",
        )
        self.depth_map_filtering_combobox.grid(
            row=7, column=4, padx=5, pady=5, sticky=W
        )

        self.out_epsg_code_label = Label(self.root, text="Output EPSG of Point Clouds:")
        self.out_epsg_code_label.grid(row=8, column=0, padx=5, pady=5, sticky=W)
        self.out_epsg_code_entry = Entry(self.root)
        self.out_epsg_code_tooltip = Hovertip(
            self.out_epsg_code_entry,
            "Defines the output coordinate system. Use EPSG digits.",
        )
        self.out_epsg_code_entry.grid(row=8, column=1, padx=5, pady=5, sticky=W)
        self.out_epsg_code_button = Button(self.root, text="...", width=2)
        # TODO: Add EPSG selection helper.
        self.out_epsg_code_button.grid(row=8, column=2, padx=5, pady=5, sticky=W)

        self.run_button = Button(self.root, text="Run FACA", command=self.run_faca)
        self.run_button.grid(row=9, column=0, padx=5, pady=5, sticky=W)

        self.save_to_ini_button = Button(
            self.root,
            text="Save Settings to file...",
            command=self.on_save_to_ini_button_clicked,
        )
        self.save_to_ini_button.grid(row=9, column=1, padx=5, pady=5, sticky=W)

        self.exit_button = Button(self.root, text="Exit", command=self.root.destroy)
        self.exit_button.grid(row=9, column=5, padx=5, pady=5, sticky=W)

        progress = Progressbar(self.root, orient="horizontal", length=1200)
        progress.grid(row=11, column=0, padx=5, pady=5, sticky="nsew", columnspan=6)

    def update_ui_with_ini_section(self, event) -> None:
        """Called when self.ini_section_combobox changes AND when a new .ini file is selected.
        event is necessary to make the function callable when the combobox changes."""
        ini_handle = configparser.ConfigParser()
        ini_handle.read(self.ini_file)
        section = self.ini_section_combobox.get()
        self._replace_entry(
            self.project_name_entry, ini_handle[section]["project_name"]
        )
        self._replace_entry(self.in_path_entry, ini_handle[section]["input_image_dir"])
        self._replace_entry(self.out_path_entry, ini_handle[section]["output_dir"])
        self.alignment_accuracy_combobox.current(
            self._get_alignment_accuracy_index(
                ini_handle[section]["alignment_accuracy"]
            )
        )
        self._update_camera_accuracy(ini_handle[section]["camera_accuracy"])
        self._replace_entry(
            self.keypoint_limit_entry, ini_handle[section]["keypoint_limit"]
        )
        self._replace_entry(
            self.tiepoint_limit_entry, ini_handle[section]["tiepoint_limit"]
        )
        self._update_criterions(
            ini_handle[section]["criterions"], ini_handle[section]["criterion_values"]
        )
        self.depth_map_quality_combobox.current(
            self._get_depth_map_quality_index(ini_handle[section]["depth_map_quality"])
        )
        self.depth_map_filtering_combobox.current(
            self._get_depth_map_filtering_index(
                ini_handle[section]["depth_map_filtering"]
            )
        )
        self._replace_entry(
            self.out_epsg_code_entry, ini_handle[section]["output_epsg_code"]
        )

    def _get_alignment_accuracy_index(self, ini_value: str) -> int:
        # 0 - Highest, 1 - High, 2 - Medium, 4 - Low, 8 - Lowest
        # 0, 1 and 2 align with their indexes in the combobox
        if ini_value in ("0", "1", "2"):
            return int(ini_value)
        elif ini_value == "4":
            return 3
        elif ini_value == "8":
            return 4

    def _update_camera_accuracy(self, ini_value: str) -> None:
        if ini_value == "None":
            self.camera_accuracy_combobox.current(0)
        elif ini_value == "EXIF":
            self.camera_accuracy_combobox.current(1)
        else:
            self.camera_accuracy_combobox.current(2)
        self.on_camera_accuracy_combobox_changed(self.camera_accuracy_combobox.get())
        # replace entry only writtes into the entry if "Custom" is selected by
        # on_camera_accuracy_combobox_changed bc otherwise its disabled.
        self._replace_entry(self.camera_accuracy_entry, ini_value)

    def _update_criterions(self, criterions: str, values: str) -> None:
        for checkbutton in (
            self.image_count_checkbutton,
            self.projection_accuracy_checkbutton,
            self.reconstruction_uncertainty_checkbutton,
            self.reprojection_error_checkbutton,
        ):
            if "selected" in checkbutton.state():
                checkbutton.invoke()
        if criterions == "None":
            return
        criterions_with_values = list(zip(criterions.split(","), values.split(",")))
        for c, v in criterions_with_values:
            if c == "ImageCount":
                self.image_count_checkbutton.invoke()
                self._replace_entry(self.image_count_entry, v)
            elif c == "ProjectionAccuracy":
                self.projection_accuracy_checkbutton.invoke()
                self._replace_entry(self.projection_accuracy_entry, v)
            elif c == "ReconstructionUncertainty":
                self.reconstruction_uncertainty_checkbutton.invoke()
                self._replace_entry(self.reconstruction_uncertainty_entry, v)
            elif c == "ReprojectionError":
                self.reprojection_error_checkbutton.invoke()
                self._replace_entry(self.reprojection_error_entry, v)

    def _get_depth_map_quality_index(self, ini_value: str) -> int:
        # 1 - Ultra high, 2 - High, 4 - Medium, 8 - Low, 16 - Lowest.
        if ini_value == "1":
            return 0
        elif ini_value == "2":
            return 1
        elif ini_value == "4":
            return 2
        elif ini_value == "8":
            return 3
        elif ini_value == "16":
            return 4

    def _get_depth_map_filtering_index(self, ini_value: str) -> int:
        if ini_value == "NoFiltering":
            return 0
        elif ini_value == "MildFiltering":
            return 1
        elif ini_value == "ModerateFiltering":
            return 2
        elif ini_value == "AggressiveFiltering":
            return 3

    def validate_ui(self) -> bool:
        """There is another _validate function inside the calculation.
        This one is just to make sure there are no typos and empty entry fields.
        We don't need to check the comboboxes and checkbuttons as these can only have valid values.
        """
        valid = True
        if not self.project_name_entry.get():
            valid = False
        if not os.path.isdir(self.in_path_entry.get()):
            valid = False
        if not self.out_path_entry.get():
            valid = False
        if (
            self.camera_accuracy_combobox.get() not in ("Default (10 m)", "Use Exif")
            and not self.camera_accuracy_entry.get()
        ):
            valid = False
        if not self.keypoint_limit_entry.get():
            valid = False
        if not self.tiepoint_limit_entry.get():
            valid = False
        if self.image_count_checkbutton.state() and not self.image_count_entry.get():
            valid = False
        if (
            self.projection_accuracy_checkbutton.state()
            and not self.projection_accuracy_entry.get()
        ):
            valid = False
        if (
            self.reconstruction_uncertainty_checkbutton.state()
            and not self.reconstruction_uncertainty_entry.get()
        ):
            valid = False
        if (
            self.reprojection_error_checkbutton.state()
            and not self.reprojection_error_entry.get()
        ):
            valid = False
        if not self.out_epsg_code_entry.get():
            valid = False
        return valid

    def get_settings_from_ui(self) -> dict:
        settings_dict = {}
        settings_dict["project_name"] = self.project_name_entry.get()
        settings_dict["input_image_dir"] = self.in_path_entry.get()
        settings_dict["output_dir"] = self.out_path_entry.get()
        settings_dict["alignment_accuracy"] = int(
            self.alignment_accuracy_combobox.get()[0]
        )
        # First sign in combobox is the correct integer.
        settings_dict["camera_accuracy"] = self._get_camera_accuracy(
            self.camera_accuracy_combobox.get()
        )
        settings_dict["keypoint_limit"] = int(self.keypoint_limit_entry.get())
        settings_dict["tiepoint_limit"] = int(self.tiepoint_limit_entry.get())
        settings_dict["criterions"] = self._get_criterions()
        settings_dict["criterion_values"] = self._get_criterion_values()
        settings_dict["depth_map_quality"] = self._get_depth_map_quality(
            self.depth_map_quality_combobox.get()
        )
        settings_dict["depth_map_filtering"] = self._get_depth_map_filtering(
            self.depth_map_filtering_combobox.get()
        )
        settings_dict["output_epsg_code"] = int(self.out_epsg_code_entry.get())
        return settings_dict

    def _get_camera_accuracy(self, ca_string) -> str:
        if ca_string.startswith("Default"):
            return "None"
        elif ca_string.startswith("Use Exif"):
            return "EXIF"
        else:  # Custom Mode
            return self.camera_accuracy_entry.get()

    def _get_criterions(self) -> str:
        criterions_str = ""
        if self.image_count_checkbutton.state():
            criterions_str = ",".join(filter(None, (criterions_str, "ImageCount")))
        if self.projection_accuracy_checkbutton.state():
            criterions_str = ",".join(
                filter(None, (criterions_str, "ProjectionAccuracy"))
            )
        if self.reconstruction_uncertainty_checkbutton.state():
            criterions_str = ",".join(
                filter(None, (criterions_str, "ReconstructionUncertainty"))
            )
        if self.reprojection_error_checkbutton.state():
            criterions_str = ",".join(
                filter(None, (criterions_str, "ReprojectionError"))
            )
        if not criterions_str:
            criterions_str = "None"
        return criterions_str

    def _get_criterion_values(self) -> str:
        criterion_values_str = ""
        image_count_value = self.image_count_entry.get()
        projection_accuracy_value = self.projection_accuracy_entry.get()
        reconstruction_uncertainty_value = self.reconstruction_uncertainty_entry.get()
        reprojection_error_value = self.reprojection_error_entry.get()
        if image_count_value:
            criterion_values_str = ",".join(
                filter(None, (criterion_values_str, image_count_value))
            )
        if projection_accuracy_value:
            criterion_values_str = ",".join(
                filter(None, (criterion_values_str, projection_accuracy_value))
            )
        if reconstruction_uncertainty_value:
            criterion_values_str = ",".join(
                filter(None, (criterion_values_str, reconstruction_uncertainty_value))
            )
        if reprojection_error_value:
            criterion_values_str = ",".join(
                filter(None, (criterion_values_str, reprojection_error_value))
            )
        if not criterion_values_str:
            criterion_values_str = "None"
        return criterion_values_str

    def _get_depth_map_quality(self, dq_string) -> str:
        if dq_string == "1 - Ultra high":
            return 1
        elif dq_string == "2 - High":
            return 2
        elif dq_string == "4 - Medium":
            return 4
        elif dq_string == "8 - Low":
            return 8
        elif dq_string == "16 - Lowest":
            return 16

    def _get_depth_map_filtering(self, df_string) -> str:
        # No Filtering -> NoFiltering, Mild Filtering -> MildFiltering,
        # Moderate Filtering -> ModerateFiltering,
        # Aggressive Filtering -> AggressiveFiltering
        return df_string.replace(" ", "")

    def update_ini_section_combobox(self, ini_file="faca.ini") -> None:
        """Adds Section titles from ini_file to ini_section_combobox AND selects first one."""
        self.ini_section_combobox["values"] = self._get_sections_from_ini(ini_file)
        self.ini_section_combobox.current(0)

    def _get_sections_from_ini(self, ini_file: str) -> list:
        """Returns Section titles from ini_file."""
        ini_handle = configparser.ConfigParser()
        ini_handle.read(ini_file)
        return ini_handle.sections()

    def on_ini_path_button_clicked(self):
        ini_path = filedialog.askopenfilename(
            filetypes=[("configuration files", "*.ini")]
        )
        if ini_path:
            self._replace_entry(self.ini_path_entry, os.path.normpath(ini_path))

    def on_out_path_button_clicked(self):
        out_path = filedialog.askdirectory()
        if out_path:
            self._replace_entry(self.out_path_entry, os.path.normpath(out_path))

    def on_in_path_entry_changed(self, event) -> None:
        """Gets called when input path entry changes, either by editing the
        widget by hand or selecting a new dir trough the filedialog.
        If the new string is a directory it updates  in_path_info_label to
        show image and subdirectory counts."""
        abs_in_path = os.path.abspath(self.in_path_entry.get())
        if os.path.isdir(abs_in_path):
            image_count, subdir_count = self._get_subdir_and_image_counts(abs_in_path)
            self.in_path_info_label["text"] = (
                f"Found {image_count} .jpg files in {subdir_count} subdirectories."
            )
        else:
            self.in_path_info_label["text"] = (
                "To show image counts please select an input directory first."
            )

    def _get_subdir_and_image_counts(self, path: str) -> tuple:
        """Returns the image and (first level) subdirectory count.
        We only count images outside the top directory, because FACA expects
        every subdirectory to contain images and does not care about top level images"""
        image_count = 0
        subdir_count = 0
        top_dir = True
        for _, dirs, files in os.walk(path):
            if top_dir:
                subdir_count = len(dirs)
                top_dir = False
            else:
                image_count += sum(1 for file in files if file.lower().endswith(".jpg"))
        return image_count, subdir_count

    def on_in_path_button_clicked(self):
        in_path = filedialog.askdirectory()
        if in_path:
            self._replace_entry(self.in_path_entry, os.path.normpath(in_path))
            self.on_in_path_entry_changed(None)

    def on_camera_accuracy_combobox_changed(self, P):
        if P == "Custom":
            self.camera_accuracy_entry["state"] = "enabled"
        else:
            self._replace_entry(self.camera_accuracy_entry, "")
            self.camera_accuracy_entry["state"] = "disabled"
        return True

    def on_filter_criterions_checkbuttons_toggled(self):
        if "selected" in self.image_count_checkbutton.state():
            self.image_count_entry["state"] = "enabled"
        else:
            self._replace_entry(self.image_count_entry, "")
            self.image_count_entry["state"] = "disabled"

        if "selected" in self.projection_accuracy_checkbutton.state():
            self.projection_accuracy_entry["state"] = "enabled"
        else:
            self._replace_entry(self.projection_accuracy_entry, "")
            self.projection_accuracy_entry["state"] = "disabled"

        if "selected" in self.reconstruction_uncertainty_checkbutton.state():
            self.reconstruction_uncertainty_entry["state"] = "enabled"
        else:
            self._replace_entry(self.reconstruction_uncertainty_entry, "")
            self.reconstruction_uncertainty_entry["state"] = "disabled"

        if "selected" in self.reprojection_error_checkbutton.state():
            self.reprojection_error_entry["state"] = "enabled"
        else:
            self._replace_entry(self.reprojection_error_entry, "")
            self.reprojection_error_entry["state"] = "disabled"

    def on_save_to_ini_button_clicked(self):
        out_ini_path = filedialog.asksaveasfilename()
        if not out_ini_path:
            return
        section = self._ask_section_name()
        if not section:
            return
        if os.path.isfile(out_ini_path):
            self._append_ini(out_ini_path, section)
        else:
            self._create_ini(out_ini_path, section)

    def _ask_section_name(self) -> str:
        """Creates a new tkinter window. To ask the user to name the new section.
        Returns the stripped string of section_name_entry if "OK" selected and
        value in section_name_entry OR None if "Cancel"
        or section_name_entry is empty."""

        def on_ok_button_clicked():
            nonlocal section_name_entry_string
            section_name_entry_string = section_name_entry.get().strip()
            section_name_entry_string = (
                section_name_entry_string if section_name_entry_string else None
            )
            top.destroy()

        def on_cancel_button_clicked():
            nonlocal section_name_entry_string
            section_name_entry_string = None
            top.destroy()

        top = Toplevel(self)
        top.wm_title("Section Name?")
        section_name_label = Label(top, text="Name of the Section:")
        section_name_label.grid(row=0, column=0, padx=5, pady=5, sticky=W)
        section_name_entry = Entry(top, "")
        section_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        section_name_entry_string = None
        ok_button = Button(top, text="Ok", command=on_ok_button_clicked)
        ok_button.grid(row=1, column=0, padx=5, pady=5, sticky=W)
        cancel_button = Button(top, text="Cancel", command=on_cancel_button_clicked)
        cancel_button.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        section_name_entry.focus_set()
        top.wait_window(top)
        return section_name_entry_string

    def _append_ini(self, ini_path: str, section: str) -> None:
        out = configparser.ConfigParser()
        out.read(ini_path)
        paras = self.get_settings_from_ui()
        if out.has_section(section):
            if self._ask_replace_section(section):
                out.remove_section(section)
            else:
                return
        out.add_section(section)
        for key in paras.keys():
            out.set(section, key, str(paras[key]))
        with open(ini_path, "w") as ini_file:
            out.write(ini_file)

    def _ask_replace_section(self, section: str) -> bool:
        """Creates a new tkinter window. Asks to replace Section in .ini file."""

        def on_yes_button_clicked() -> None:
            nonlocal replace_bool
            replace_bool = True
            top.destroy()

        def on_no_button_clicked() -> None:
            nonlocal replace_bool
            replace_bool = False
            top.destroy()

        top = Toplevel(self)
        top.wm_title("Replace Section?")
        replace_label = Label(
            top, text=f"Section {section} already exists. Replace it?"
        )
        replace_label.grid(row=0, column=0, padx=5, pady=5, sticky=W)
        yes_button = Button(top, text="Yes", command=on_yes_button_clicked)
        yes_button.grid(row=1, column=0, padx=5, pady=5, sticky=W)
        no_button = Button(top, text="No", command=on_no_button_clicked)
        no_button.grid(row=1, column=1, padx=5, pady=5, sticky=W)
        replace_bool = False
        top.wait_window(top)
        return replace_bool

    def _create_ini(self, ini_path: str, section: str) -> None:
        out = configparser.ConfigParser()
        out.add_section(section)
        paras = self.get_settings_from_ui()
        for key in paras.keys():
            out.set(section, key, str(paras[key]))
        with open(ini_path, "w") as ini_file:
            out.write(ini_file)

    def run_faca(self):
        if self.validate_ui():
            settings = self.get_settings_from_ui()
            calc_Thread = multiprocessing.Process(
                target=self.thread_wrap, args=(settings,)
            )
            calc_Thread.start()

    @staticmethod
    def thread_wrap(settings: dict) -> None:
        f = FacaCalc(**settings)
        f.main()

    def _replace_entry(self, entry, new_string: str) -> None:
        """Replaces old value in entry widget with new_string.
        Mostly used by button functions."""
        entry.delete(0, END)
        entry.insert(0, new_string)

    def _val_only_int_comma(self, P):
        if str.isdigit(P.replace(",", "")) or P in ("", ","):
            return True
        else:
            return False

    def _val_only_int(self, P):
        if str.isdigit(P) or P == "":
            return True
        else:
            return False

    def _val_only_float(self, P):
        if str.isdigit(P.replace(".", "")) or P in ("", "."):
            return True
        else:
            return False
