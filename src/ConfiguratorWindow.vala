/*
 * ConfiguratorWindow.vala
 * The settings panel to manage Wine prefix utilities, plugin installer, and uninstallers.
 */

using GLib;
using Gtk;

namespace AeNux {
    public class ConfiguratorWindow : Window {
        private Label path_label;
        private Button kill_btn;
        private Button winecfg_btn;
        private Button regedit_btn;
        private Switch runner_ui_switch;

        private FileChooserButton plugin_chooser;
        private Button cep_btn;

        public ConfiguratorWindow (Gtk.Application app) {
            Object (application: app, title: "AeNux Installer");
            set_default_size (520, 420);
            window_position = WindowPosition.CENTER;
            resizable = false;

            // Header bar
            var header_bar = new HeaderBar ();
            header_bar.show_close_button = true;
            header_bar.title = "AeNux";
            header_bar.subtitle = "After Effects for Linux Installer";
            set_titlebar (header_bar);

            var notebook = new Notebook ();
            notebook.margin = 6;

            // Tab 1: General & Wine
            var general_box = new Box (Orientation.VERTICAL, 6);
            general_box.margin = 6;

            path_label = new Label ("Checking installation...");
            path_label.xalign = 0;
            path_label.ellipsize = Pango.EllipsizeMode.END;
            general_box.pack_start (path_label, false, false, 0);

            var wine_list = new ListBox ();
            wine_list.get_style_context ().add_class ("card-list");
            wine_list.set_selection_mode (SelectionMode.NONE);

            // Row 0: Winecfg and Regedit
            var row_cfg = new ListBoxRow ();
            var box_cfg = new Box (Orientation.HORIZONTAL, 6);
            box_cfg.margin = 4;
            box_cfg.pack_start (new Label ("Wine Prefix Tools:"), false, false, 0);
            winecfg_btn = new Button.with_label ("Winecfg");
            winecfg_btn.clicked.connect (() => { run_wine_tool ("winecfg"); });
            box_cfg.pack_end (winecfg_btn, false, false, 0);
            regedit_btn = new Button.with_label ("Regedit");
            regedit_btn.clicked.connect (() => { run_wine_tool ("regedit"); });
            box_cfg.pack_end (regedit_btn, false, false, 0);
            row_cfg.add (box_cfg);
            wine_list.add (row_cfg);


            // Row 2: Kill Wine Processes
            var row_kll = new ListBoxRow ();
            var box_kll = new Box (Orientation.HORIZONTAL, 6);
            box_kll.margin = 4;
            box_kll.pack_start (new Label ("Force Terminate Wine Prefix Processes:"), false, false, 0);
            kill_btn = new Button.with_label ("Kill Processes");
            kill_btn.get_style_context ().add_class ("destructive-action");
            kill_btn.clicked.connect (on_kill_clicked);
            box_kll.pack_end (kill_btn, false, false, 0);
            row_kll.add (box_kll);
            wine_list.add (row_kll);

            // Row 3: Runner UI Switch
            var row_run = new ListBoxRow ();
            var box_run = new Box (Orientation.HORIZONTAL, 6);
            box_run.margin = 4;
            box_run.pack_start (new Label ("Enable Runner Log UI:"), false, false, 0);
            runner_ui_switch = new Switch ();
            runner_ui_switch.active = (Utils.get_config_value ("show_runner_ui") != "false");
            runner_ui_switch.notify["active"].connect ((s, p) => {
                Utils.set_config_value ("show_runner_ui", runner_ui_switch.active ? "true" : "false");
            });
            box_run.pack_end (runner_ui_switch, false, false, 0);
            row_run.add (box_run);
            wine_list.add (row_run);

            general_box.pack_start (wine_list, true, true, 0);

            // Uninstall Section
            var un_list = new ListBox ();
            un_list.get_style_context ().add_class ("card-list");
            un_list.set_selection_mode (SelectionMode.NONE);

            var row_un = new ListBoxRow ();
            var box_un = new Box (Orientation.HORIZONTAL, 6);
            box_un.margin = 4;
            box_un.pack_start (new Label ("Uninstall After Effects (keeps package):"), false, false, 0);
            var ae_un_btn = new Button.with_label ("Uninstall AE");
            ae_un_btn.get_style_context ().add_class ("destructive-action");
            ae_un_btn.clicked.connect (on_uninstall_ae_clicked);
            box_un.pack_end (ae_un_btn, false, false, 0);
            row_un.add (box_un);
            un_list.add (row_un);

            var row_clean = new ListBoxRow ();
            var box_clean = new Box (Orientation.HORIZONTAL, 6);
            box_clean.margin = 4;
            box_clean.pack_start (new Label ("Complete Clean Uninstall (purges AeNux):"), false, false, 0);
            var clean_un_btn = new Button.with_label ("Clean Uninstall");
            clean_un_btn.get_style_context ().add_class ("destructive-action");
            clean_un_btn.clicked.connect (on_clean_uninstall_clicked);
            box_clean.pack_end (clean_un_btn, false, false, 0);
            row_clean.add (box_clean);
            un_list.add (row_clean);

            general_box.pack_start (un_list, false, false, 0);

            notebook.append_page (general_box, new Label ("General"));

            // Tab 2: Plugins
            var plugin_box = new Box (Orientation.VERTICAL, 6);
            plugin_box.margin = 6;

            var plug_card_list = new ListBox ();
            plug_card_list.get_style_context ().add_class ("card-list");
            plug_card_list.set_selection_mode (SelectionMode.NONE);

            var plug_size_group = new SizeGroup (SizeGroupMode.HORIZONTAL);

            // Plugin File Selection Row
            var row_plug_sel = new ListBoxRow ();
            var box_plug_sel = new Box (Orientation.HORIZONTAL, 6);
            box_plug_sel.margin = 4;
            var lbl_p1 = new Label ("Select Plugin:");
            lbl_p1.xalign = 0;
            plug_size_group.add_widget (lbl_p1);
            box_plug_sel.pack_start (lbl_p1, false, false, 0);
            plugin_chooser = new FileChooserButton ("Select Plugin or Installer", FileChooserAction.OPEN);
            var zip_filter = new FileFilter ();
            zip_filter.add_pattern ("*.aex");
            zip_filter.add_pattern ("*.exe");
            zip_filter.add_pattern ("*.zip");
            zip_filter.add_pattern ("*.tar.gz");
            zip_filter.add_pattern ("*.tgz");
            zip_filter.add_pattern ("*.tar.xz");
            zip_filter.add_pattern ("*.txz");
            zip_filter.add_pattern ("*.tar.bz2");
            zip_filter.add_pattern ("*.tbz2");
            zip_filter.add_pattern ("*.tar");
            zip_filter.add_pattern ("*.7z");
            zip_filter.add_pattern ("*.rar");
            zip_filter.set_filter_name ("Plugins, Installers & Archives (*.aex, *.exe, *.zip, ...)");
            plugin_chooser.add_filter (zip_filter);
            box_plug_sel.pack_start (plugin_chooser, true, true, 0);
            row_plug_sel.add (box_plug_sel);
            plug_card_list.add (row_plug_sel);
            plugin_chooser.selection_changed.connect (on_plugin_selected);

            plugin_box.pack_start (new Label ("<b>After Effects Plugins</b>") { use_markup = true, xalign = 0 }, false, false, 0);
            plugin_box.pack_start (plug_card_list, false, false, 0);

            // CEP Extension Section
            var cep_card_list = new ListBox ();
            cep_card_list.get_style_context ().add_class ("card-list");
            cep_card_list.set_selection_mode (SelectionMode.NONE);

            var row_cep_act = new ListBoxRow ();
            var box_cep_act = new Box (Orientation.HORIZONTAL, 6);
            box_cep_act.margin = 4;
            var lbl_c2 = new Label ("CEP Extension:");
            lbl_c2.xalign = 0;
            plug_size_group.add_widget (lbl_c2);
            box_cep_act.pack_start (lbl_c2, false, false, 0);
            cep_btn = new Button.with_label ("Import CEP Extension...");
            cep_btn.get_style_context ().add_class ("suggested-action");
            cep_btn.clicked.connect (on_cep_import_clicked);
            box_cep_act.pack_end (cep_btn, false, false, 0);
            row_cep_act.add (box_cep_act);
            cep_card_list.add (row_cep_act);

            plugin_box.pack_start (new Label ("<b>CEP Extension Support</b>") { use_markup = true, xalign = 0 }, false, false, 0);
            plugin_box.pack_start (cep_card_list, false, false, 0);

            notebook.append_page (plugin_box, new Label ("Plugins"));

            add (notebook);

            refresh_state ();
            show_all ();
        }

        public void refresh_state () {
            string? user_location = Utils.get_config_value ("user_location");
            if (user_location != null) {
                path_label.label = "Installation Path: " + user_location;
                winecfg_btn.sensitive = true;
                regedit_btn.sensitive = true;
                kill_btn.sensitive = true;
                runner_ui_switch.sensitive = true;
                plugin_chooser.sensitive = true;
                cep_btn.sensitive = true;
            } else {
                path_label.label = "AeNux is not installed yet. Go to the Installer page.";
                winecfg_btn.sensitive = false;
                regedit_btn.sensitive = false;
                kill_btn.sensitive = false;
                runner_ui_switch.sensitive = false;
                plugin_chooser.sensitive = false;
                cep_btn.sensitive = false;
            }
        }

        private void run_wine_tool (string tool) {
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");
            if (wineprefix != null && wine_path != null) {
                string wine_bin = Path.build_filename (wine_path, "files", "bin", "wine");
                string[] env = Utils.get_wine_env (wine_path, wineprefix);
                
                new Thread<int> ("wine-tool-runner", () => {
                    string? o, e;
                    Utils.run_command ({wine_bin, tool}, env, null, out o, out e);
                    return 0;
                });
            }
        }



        private void on_kill_clicked () {
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");
            if (wineprefix != null && wine_path != null) {
                if (Utils.kill_wine_processes (wine_path, wineprefix)) {
                    var d = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.OK, "Wineprefix processes terminated successfully.");
                    d.run ();
                    d.destroy ();
                }
            }
        }

        private void run_wine_exe (string exe_path) {
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");
            if (wineprefix != null && wine_path != null) {
                string wine_bin = Path.build_filename (wine_path, "files", "bin", "wine");
                string[] env = Utils.get_wine_env (wine_path, wineprefix);
                
                var progress_dialog = new MessageDialog (
                    this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.NONE,
                    "Running plugin installer via Wine..."
                );
                progress_dialog.show_all ();

                new Thread<int> ("wine-exe-installer", () => {
                    string? o, e;
                    Utils.run_command ({wine_bin, exe_path}, env, null, out o, out e);
                    
                    Idle.add (() => {
                        progress_dialog.destroy ();
                        var d = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.OK, "Finished running Wine plugin installer: " + Path.get_basename (exe_path));
                        d.run ();
                        d.destroy ();
                        return false;
                    });
                    return 0;
                });
            }
        }

        private void on_plugin_selected () {
            string path = plugin_chooser.get_filename ();
            if (path == null) return;

            string? aenux_path = Utils.get_config_value ("aenux_path");
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");

            if (aenux_path == null || wineprefix == null || wine_path == null) return;

            string plugins_dir = Path.build_filename (aenux_path, "Plug-ins");
            DirUtils.create_with_parents (plugins_dir, 0755);

            string basename = Path.get_basename (path);
            string dest_path = Path.build_filename (plugins_dir, basename);
            string ext = path.down ();

            if (ext.has_suffix (".aex") || ext.has_suffix (".exe")) {
                if (FileUtils.test (dest_path, FileTest.EXISTS)) {
                    var confirm = new MessageDialog (
                        this, DialogFlags.MODAL, MessageType.QUESTION, ButtonsType.YES_NO,
                        "The plugin '%s' already exists in the Plug-ins folder. Do you want to overwrite it?".printf (basename)
                    );
                    int res = confirm.run ();
                    confirm.destroy ();
                    if (res != ResponseType.YES) {
                        plugin_chooser.unselect_all ();
                        return;
                    }
                }
            }

            // Perform installation
            if (ext.has_suffix (".exe")) {
                run_wine_exe (path);
            } else if (ext.has_suffix (".aex")) {
                if (Utils.copy_file (path, dest_path)) {
                    var d = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.OK, "Plugin '%s' installed successfully.".printf (basename));
                    d.run ();
                    d.destroy ();
                } else {
                    var d = new MessageDialog (this, DialogFlags.MODAL, MessageType.ERROR, ButtonsType.OK, "Failed to copy plugin '%s'.".printf (basename));
                    d.run ();
                    d.destroy ();
                }
            } else {
                // Assume archive, extract
                var d = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.NONE, "Extracting plugin archive...");
                d.show_all ();
                new Thread<int> ("plugin-worker", () => {
                    bool success = Utils.extract_archive (path, plugins_dir);
                    Idle.add (() => {
                        d.destroy ();
                        var res_dialog = new MessageDialog (
                            this, DialogFlags.MODAL,
                            success ? MessageType.INFO : MessageType.ERROR,
                            ButtonsType.OK,
                            success ? "Archive extracted successfully!" : "Failed to extract archive."
                        );
                        res_dialog.run ();
                        res_dialog.destroy ();
                        return false;
                    });
                    return 0;
                });
            }

            plugin_chooser.unselect_all ();
        }

        private void on_cep_import_clicked () {
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");
            if (wineprefix == null || wine_path == null) return;

            var choice_dialog = new MessageDialog (
                this, DialogFlags.MODAL, MessageType.QUESTION, ButtonsType.NONE,
                "Select CEP Extension Import Mode"
            );
            choice_dialog.add_button ("Import ZXP File", 1);
            choice_dialog.add_button ("Import Extension Folder", 2);
            choice_dialog.add_button ("Cancel", ResponseType.CANCEL);

            int choice = choice_dialog.run ();
            choice_dialog.destroy ();

            if (choice == ResponseType.CANCEL) {
                return;
            }

            if (choice == 1) {
                var filter = new FileFilter ();
                filter.set_name ("Adobe ZXP Extensions (*.zxp)");
                filter.add_pattern ("*.zxp");
                filter.add_pattern ("*.ZXP");

                var file_chooser = new FileChooserDialog (
                    "Select ZXP File", this, FileChooserAction.OPEN,
                    "Cancel", ResponseType.CANCEL,
                    "Open", ResponseType.ACCEPT
                );
                file_chooser.add_filter (filter);

                int res = file_chooser.run ();
                if (res == ResponseType.ACCEPT) {
                    string zxp_path = file_chooser.get_filename ();
                    file_chooser.destroy ();

                    string basename = Path.get_basename (zxp_path);
                    string name_without_ext = basename;
                    if (basename.down ().has_suffix (".zxp")) {
                        name_without_ext = basename.substring (0, basename.length - 4);
                    }

                    var info_dialog = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.NONE, "Extracting ZXP extension...");
                    info_dialog.show_all ();

                    new Thread<int> ("cep-zxp-worker", () => {
                        string cep_dir = Path.build_filename (wineprefix, "drive_c", "Program Files (x86)", "Common Files", "Adobe", "CEP", "extensions");
                        string cep_dir_64 = Path.build_filename (wineprefix, "drive_c", "Program Files", "Common Files", "Adobe", "CEP", "extensions");
                        DirUtils.create_with_parents (cep_dir, 0755);
                        DirUtils.create_with_parents (cep_dir_64, 0755);

                        string dest_dir = Path.build_filename (cep_dir, name_without_ext);
                        string dest_dir_64 = Path.build_filename (cep_dir_64, name_without_ext);

                        bool s1 = Utils.extract_archive (zxp_path, dest_dir);
                        bool s2 = Utils.extract_archive (zxp_path, dest_dir_64);

                        Idle.add (() => {
                            info_dialog.destroy ();
                            var result_dialog = new MessageDialog (
                                this, DialogFlags.MODAL,
                                (s1 || s2) ? MessageType.INFO : MessageType.ERROR,
                                ButtonsType.OK,
                                (s1 || s2) ? "ZXP Extension imported successfully!" : "Failed to extract ZXP extension."
                            );
                            result_dialog.run ();
                            result_dialog.destroy ();
                            return false;
                        });
                        return 0;
                    });
                } else {
                    file_chooser.destroy ();
                }
            } else if (choice == 2) {
                var folder_chooser = new FileChooserDialog (
                    "Select Extension Folder", this, FileChooserAction.SELECT_FOLDER,
                    "Cancel", ResponseType.CANCEL,
                    "Select", ResponseType.ACCEPT
                );

                int res = folder_chooser.run ();
                if (res == ResponseType.ACCEPT) {
                    string folder_path = folder_chooser.get_filename ();
                    folder_chooser.destroy ();

                    string basename = Path.get_basename (folder_path);

                    var info_dialog = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.NONE, "Importing extension folder...");
                    info_dialog.show_all ();

                    new Thread<int> ("cep-folder-worker", () => {
                        string cep_dir = Path.build_filename (wineprefix, "drive_c", "Program Files (x86)", "Common Files", "Adobe", "CEP", "extensions");
                        string cep_dir_64 = Path.build_filename (wineprefix, "drive_c", "Program Files", "Common Files", "Adobe", "CEP", "extensions");
                        DirUtils.create_with_parents (cep_dir, 0755);
                        DirUtils.create_with_parents (cep_dir_64, 0755);

                        string dest_dir = Path.build_filename (cep_dir, basename);
                        string dest_dir_64 = Path.build_filename (cep_dir_64, basename);

                        bool s1 = Utils.copy_directory (folder_path, dest_dir);
                        bool s2 = Utils.copy_directory (folder_path, dest_dir_64);

                        Idle.add (() => {
                            info_dialog.destroy ();
                            var result_dialog = new MessageDialog (
                                this, DialogFlags.MODAL,
                                (s1 || s2) ? MessageType.INFO : MessageType.ERROR,
                                ButtonsType.OK,
                                (s1 || s2) ? "Extension folder imported successfully!" : "Failed to copy extension folder."
                            );
                            result_dialog.run ();
                            result_dialog.destroy ();
                            return false;
                        });
                        return 0;
                    });
                } else {
                    folder_chooser.destroy ();
                }
            }
        }

        private void on_uninstall_ae_clicked () {
            string? user_location = Utils.get_config_value ("user_location");
            if (user_location == null) return;

            var confirm = new MessageDialog (
                this, DialogFlags.MODAL, MessageType.QUESTION, ButtonsType.YES_NO,
                "Are you sure you want to uninstall After Effects?\nThis will remove Wineprefix, custom Wine, and After Effects directories, but leaves the Aenux software package intact."
            );
            int res = confirm.run ();
            confirm.destroy ();

            if (res == ResponseType.YES) {
                string? o, e;
                Utils.run_command ({"rm", "-rf", user_location}, null, null, out o, out e);
                
                // Revert user shortcuts overrides (returns configuration back to "Installer" state)
                Utils.delete_desktop_overrides ();

                // Delete local configuration file
                string config_path = Utils.get_config_path ();
                if (FileUtils.test (config_path, FileTest.EXISTS)) {
                    FileUtils.remove (config_path);
                }

                var finished = new MessageDialog (this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.OK, "After Effects uninstalled successfully.");
                finished.run ();
                finished.destroy ();

                // Launch Installer Page and close self
                var app = (Gtk.Application) this.application;
                var installer_win = new InstallerWindow (app);
                app.add_window (installer_win);
                installer_win.present ();
                
                this.close ();
            }
        }

        private void on_clean_uninstall_clicked () {
            var confirm = new MessageDialog (
                this, DialogFlags.MODAL, MessageType.QUESTION, ButtonsType.YES_NO,
                "Are you sure you want to clean uninstall AeNux?\nThis will completely purge all After Effects folders, Wineprefixes, settings, shortcuts, and remove the Aenux package itself."
            );
            int res = confirm.run ();
            confirm.destroy ();

            if (res == ResponseType.YES) {
                this.close ();
                Utils.perform_clean_remove ();
            }
        }
    }
}
