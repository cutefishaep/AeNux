/*
 * InstallerWindow.vala
 * Installer window for AeNux — downloads Wine, After Effects, and sets up the prefix.
 */

using GLib;
using Gtk;

namespace AeNux {
    public class InstallerWindow : Gtk.ApplicationWindow {

        private Gtk.Label top_title_label;
        private Gtk.ProgressBar progress_bar;
        private Gtk.Button cancel_button;

        private Gtk.Stack wizard_stack;
        
        // Page 1 fields
        private Gtk.Entry install_dir_entry;
        
        // Page 2 fields
        private Gtk.Entry ae_archive_entry;
        
        // Page 3 fields
        private Gtk.Entry xml3_entry;
        private Gtk.Entry xml3r_entry;

        // Logs
        private Gtk.ScrolledWindow log_scroll;
        private Gtk.TextView log_view;
        private Gtk.TextBuffer log_buffer;
        private FileStream? log_file = null;

        private bool cancelled = false;
        private string? install_dir = null;
        private string? ae_archive_path = null;
        private string? msxml3_path = null;
        private string? msxml3r_path = null;

        public InstallerWindow (Gtk.Application app) {
            Object (application: app, title: "AeNux Installer", default_width: 350, default_height: 520);
        }

        construct {
            set_resizable (false);
            set_border_width (0);
            window_position = WindowPosition.CENTER;

            // Main vertical layout
            var main_vbox = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);

            // Top bar box
            var top_box = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 8);
            top_box.set_margin_start (16);
            top_box.set_margin_end (16);
            top_box.set_margin_top (16);
            top_box.set_margin_bottom (8);

            top_title_label = new Gtk.Label ("AeNux Installer");
            top_title_label.get_style_context ().add_class ("title-label");
            top_title_label.set_halign (Gtk.Align.START);
            top_box.pack_start (top_title_label, true, true, 0);

            cancel_button = new Gtk.Button.with_label ("Cancel");
            cancel_button.clicked.connect (on_cancel_clicked);
            top_box.pack_end (cancel_button, false, false, 0);

            main_vbox.pack_start (top_box, false, false, 0);

            // Progress bar
            progress_bar = new Gtk.ProgressBar ();
            progress_bar.get_style_context ().add_class ("aenux-progress");
            main_vbox.pack_start (progress_bar, false, false, 0);

            // Content area
            var content_vbox = new Gtk.Box (Gtk.Orientation.VERTICAL, 12);
            content_vbox.set_margin_start (20);
            content_vbox.set_margin_end (20);
            content_vbox.set_margin_top (20);
            content_vbox.set_margin_bottom (16);
            content_vbox.set_vexpand (true);

            // Center Logo & Text with top and bottom spacing
            var logo_image = load_logo_image ();
            logo_image.set_halign (Gtk.Align.CENTER);
            logo_image.set_margin_top (12);
            content_vbox.pack_start (logo_image, false, false, 0);

            var logo_label = new Gtk.Label ("AeNux");
            logo_label.get_style_context ().add_class ("logo-text");
            logo_label.set_halign (Gtk.Align.CENTER);
            logo_label.set_margin_bottom (20);
            content_vbox.pack_start (logo_label, false, false, 0);

            // Stack for different steps
            wizard_stack = new Gtk.Stack ();
            wizard_stack.set_transition_type (Gtk.StackTransitionType.SLIDE_LEFT_RIGHT);
            wizard_stack.set_transition_duration (300);
            wizard_stack.set_vexpand (true);

            // PAGE 1: Select Installation Folder
            var page1_box = new Gtk.Box (Gtk.Orientation.VERTICAL, 8);
            page1_box.set_vexpand (true);
            
            // Fixed-width centered container for step content
            var p1_input_container = new Gtk.Box (Gtk.Orientation.VERTICAL, 6);
            p1_input_container.set_halign (Gtk.Align.CENTER);
            p1_input_container.set_size_request (280, -1);

            var page1_title = new Gtk.Label ("Select Installation Folder");
            page1_title.get_style_context ().add_class ("step-title");
            page1_title.set_halign (Gtk.Align.START);
            p1_input_container.pack_start (page1_title, false, false, 0);

            var folder_row = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 6);
            install_dir_entry = new Gtk.Entry ();
            install_dir_entry.set_text (Path.build_filename (Environment.get_home_dir (), "AeNux"));
            install_dir_entry.set_hexpand (true);
            install_dir_entry.set_width_chars (22);
            folder_row.pack_start (install_dir_entry, true, true, 0);

            var folder_browse_btn = new Gtk.Button.with_label ("Browse...");
            folder_browse_btn.clicked.connect (on_select_install_dir);
            folder_row.pack_start (folder_browse_btn, false, false, 0);
            p1_input_container.pack_start (folder_row, false, false, 0);
            
            page1_box.pack_start (p1_input_container, false, false, 0);

            // Expanding spacer
            var p1_spacer = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);
            p1_spacer.set_vexpand (true);
            page1_box.pack_start (p1_spacer, true, true, 0);

            // Centered Next Button Box
            var page1_nav = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 0);
            page1_nav.set_halign (Gtk.Align.CENTER);
            var page1_next_btn = new Gtk.Button.with_label ("Next");
            page1_next_btn.get_style_context ().add_class ("suggested-action");
            page1_next_btn.clicked.connect (() => {
                wizard_stack.set_visible_child_name ("page2");
            });
            page1_nav.pack_start (page1_next_btn, false, false, 0);
            page1_box.pack_start (page1_nav, false, false, 0);

            wizard_stack.add_named (page1_box, "page1");

            // PAGE 2: Select After Effects Archive
            var page2_box = new Gtk.Box (Gtk.Orientation.VERTICAL, 8);
            page2_box.set_vexpand (true);
            
            var p2_input_container = new Gtk.Box (Gtk.Orientation.VERTICAL, 6);
            p2_input_container.set_halign (Gtk.Align.CENTER);
            p2_input_container.set_size_request (280, -1);

            var page2_title = new Gtk.Label ("Select After Effects Archive (.7z/.zip/.rar)");
            page2_title.get_style_context ().add_class ("step-title");
            page2_title.set_halign (Gtk.Align.START);
            p2_input_container.pack_start (page2_title, false, false, 0);

            var archive_row = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 6);
            ae_archive_entry = new Gtk.Entry ();
            ae_archive_entry.set_editable (false);
            ae_archive_entry.set_placeholder_text ("No file selected...");
            ae_archive_entry.set_hexpand (true);
            ae_archive_entry.set_width_chars (22);
            archive_row.pack_start (ae_archive_entry, true, true, 0);

            var archive_browse_btn = new Gtk.Button.with_label ("Browse...");
            archive_browse_btn.clicked.connect (on_select_ae_archive);
            archive_row.pack_start (archive_browse_btn, false, false, 0);
            p2_input_container.pack_start (archive_row, false, false, 0);
            
            page2_box.pack_start (p2_input_container, false, false, 0);

            // Expanding spacer
            var p2_spacer = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);
            p2_spacer.set_vexpand (true);
            page2_box.pack_start (p2_spacer, true, true, 0);

            // Centered Nav Buttons Box
            var page2_nav = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 8);
            page2_nav.set_halign (Gtk.Align.CENTER);
            var page2_back_btn = new Gtk.Button.with_label ("Back");
            page2_back_btn.clicked.connect (() => {
                wizard_stack.set_visible_child_name ("page1");
            });
            page2_nav.pack_start (page2_back_btn, false, false, 0);

            var page2_next_btn = new Gtk.Button.with_label ("Next");
            page2_next_btn.get_style_context ().add_class ("suggested-action");
            page2_next_btn.clicked.connect (() => {
                wizard_stack.set_visible_child_name ("page3");
            });
            page2_nav.pack_start (page2_next_btn, false, false, 0);
            page2_box.pack_start (page2_nav, false, false, 0);

            wizard_stack.add_named (page2_box, "page2");

            // PAGE 3: Select DLLs
            var page3_box = new Gtk.Box (Gtk.Orientation.VERTICAL, 8);
            page3_box.set_vexpand (true);
            
            var p3_input_container = new Gtk.Box (Gtk.Orientation.VERTICAL, 6);
            p3_input_container.set_halign (Gtk.Align.CENTER);
            p3_input_container.set_size_request (280, -1);

            var page3_title = new Gtk.Label ("Select Required DLL Files");
            page3_title.get_style_context ().add_class ("step-title");
            page3_title.set_halign (Gtk.Align.START);
            p3_input_container.pack_start (page3_title, false, false, 0);

            var dll_grid = new Gtk.Grid ();
            dll_grid.set_row_spacing (6);
            dll_grid.set_column_spacing (6);

            var xml3_label = new Gtk.Label ("msxml3.dll:");
            xml3_label.set_halign (Gtk.Align.START);
            xml3_entry = new Gtk.Entry ();
            xml3_entry.set_editable (false);
            xml3_entry.set_placeholder_text ("No file selected...");
            xml3_entry.set_width_chars (20);
            var xml3_btn = new Gtk.Button.with_label ("Browse...");
            xml3_btn.clicked.connect (on_select_msxml3);

            dll_grid.attach (xml3_label, 0, 0, 1, 1);
            dll_grid.attach (xml3_entry, 1, 0, 1, 1);
            dll_grid.attach (xml3_btn, 2, 0, 1, 1);

            var xml3r_label = new Gtk.Label ("msxml3r.dll:");
            xml3r_label.set_halign (Gtk.Align.START);
            xml3r_entry = new Gtk.Entry ();
            xml3r_entry.set_editable (false);
            xml3r_entry.set_placeholder_text ("No file selected...");
            xml3r_entry.set_width_chars (20);
            var xml3r_btn = new Gtk.Button.with_label ("Browse...");
            xml3r_btn.clicked.connect (on_select_msxml3r);

            dll_grid.attach (xml3r_label, 0, 1, 1, 1);
            dll_grid.attach (xml3r_entry, 1, 1, 1, 1);
            dll_grid.attach (xml3r_btn, 2, 1, 1, 1);

            p3_input_container.pack_start (dll_grid, false, false, 0);
            page3_box.pack_start (p3_input_container, false, false, 0);

            // Expanding spacer
            var p3_spacer = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);
            p3_spacer.set_vexpand (true);
            page3_box.pack_start (p3_spacer, true, true, 0);

            // Centered Nav Buttons Box
            var page3_nav = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 8);
            page3_nav.set_halign (Gtk.Align.CENTER);
            var page3_back_btn = new Gtk.Button.with_label ("Back");
            page3_back_btn.clicked.connect (() => {
                wizard_stack.set_visible_child_name ("page2");
            });
            page3_nav.pack_start (page3_back_btn, false, false, 0);

            var page3_install_btn = new Gtk.Button.with_label ("Install");
            page3_install_btn.get_style_context ().add_class ("suggested-action");
            page3_install_btn.clicked.connect (on_install_clicked);
            page3_nav.pack_start (page3_install_btn, false, false, 0);
            page3_box.pack_start (page3_nav, false, false, 0);

            wizard_stack.add_named (page3_box, "page3");

            // PAGE 4: Installing
            var page4_box = new Gtk.Box (Gtk.Orientation.VERTICAL, 8);
            page4_box.set_vexpand (true);

            // Compact console log view
            log_buffer = new Gtk.TextBuffer (null);
            log_view = new Gtk.TextView.with_buffer (log_buffer);
            log_view.set_editable (false);
            log_view.set_cursor_visible (false);
            log_view.set_wrap_mode (Gtk.WrapMode.WORD_CHAR);
            log_view.set_monospace (true);

            log_scroll = new Gtk.ScrolledWindow (null, null);
            log_scroll.set_policy (Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC);
            log_scroll.add (log_view);
            log_scroll.set_shadow_type (Gtk.ShadowType.IN);
            log_scroll.set_size_request (300, 120);
            log_scroll.set_halign (Gtk.Align.CENTER);
            
            page4_box.pack_start (log_scroll, false, false, 6);

            // Expanding spacer
            var p4_spacer = new Gtk.Box (Gtk.Orientation.VERTICAL, 0);
            p4_spacer.set_vexpand (true);
            page4_box.pack_start (p4_spacer, true, true, 0);

            // Cancel button centered at the very bottom
            var install_cancel_box = new Gtk.Box (Gtk.Orientation.HORIZONTAL, 0);
            install_cancel_box.set_halign (Gtk.Align.CENTER);
            var install_cancel_btn = new Gtk.Button.with_label ("Cancel");
            install_cancel_btn.clicked.connect (on_cancel_clicked);
            install_cancel_box.pack_start (install_cancel_btn, false, false, 0);
            page4_box.pack_start (install_cancel_box, false, false, 0);

            wizard_stack.add_named (page4_box, "page4");

            content_vbox.pack_start (wizard_stack, true, true, 0);
            main_vbox.pack_start (content_vbox, true, true, 0);

            add (main_vbox);
            
            // Auto-detect files in Downloads
            auto_detect_files ();
        }

        private Gtk.Image load_logo_image () {
            string[] paths = {
                "asset/aenux.svg",
                "/usr/share/icons/hicolor/scalable/apps/aenux.svg",
                "/opt/aenux/aenux.svg"
            };
            foreach (var path in paths) {
                if (FileUtils.test (path, FileTest.EXISTS)) {
                    try {
                        var pixbuf = new Gdk.Pixbuf.from_file_at_size (path, 64, 64);
                        return new Gtk.Image.from_pixbuf (pixbuf);
                    } catch (Error e) {
                        // ignore and try next
                    }
                }
            }
            return new Gtk.Image.from_icon_name ("aenux", Gtk.IconSize.DIALOG);
        }

        private void auto_detect_files () {
            string downloads = Path.build_filename (Environment.get_home_dir (), "Downloads");
            if (FileUtils.test (downloads, FileTest.IS_DIR)) {
                // Try to find AE archive
                string[] ae_patterns = {"AfterEffects.7z", "AfterEffects.zip", "AfterEffects.rar", "AE.7z", "AE.zip", "AE.rar", "2024.7z"};
                foreach (var p in ae_patterns) {
                    string path = Path.build_filename (downloads, p);
                    if (FileUtils.test (path, FileTest.EXISTS)) {
                        ae_archive_path = path;
                        ae_archive_entry.set_text (path);
                        append_log ("[AUTO-DETECT] Found After Effects archive: " + path);
                        break;
                    }
                }
                
                // Try to find msxml3.dll
                string path_xml3 = Path.build_filename (downloads, "msxml3.dll");
                if (FileUtils.test (path_xml3, FileTest.EXISTS)) {
                    msxml3_path = path_xml3;
                    xml3_entry.set_text (path_xml3);
                    append_log ("[AUTO-DETECT] Found msxml3.dll: " + path_xml3);
                }
                
                // Try to find msxml3r.dll
                string path_xml3r = Path.build_filename (downloads, "msxml3r.dll");
                if (FileUtils.test (path_xml3r, FileTest.EXISTS)) {
                    msxml3r_path = path_xml3r;
                    xml3r_entry.set_text (path_xml3r);
                    append_log ("[AUTO-DETECT] Found msxml3r.dll: " + path_xml3r);
                }
            }
        }

        private void on_select_install_dir () {
            var dialog = new Gtk.FileChooserDialog (
                "Select Installation Directory",
                this,
                Gtk.FileChooserAction.SELECT_FOLDER,
                "_Cancel", Gtk.ResponseType.CANCEL,
                "_Open", Gtk.ResponseType.ACCEPT
            );
            if (dialog.run () == Gtk.ResponseType.ACCEPT) {
                string path = dialog.get_filename ();
                install_dir_entry.set_text (path);
                append_log ("[SELECT] Installation directory: " + path);
            }
            dialog.destroy ();
        }

        private void on_select_ae_archive () {
            var dialog = new Gtk.FileChooserDialog (
                "Select After Effects Archive (.7z, .zip, .rar)",
                this,
                Gtk.FileChooserAction.OPEN,
                "_Cancel", Gtk.ResponseType.CANCEL,
                "_Open", Gtk.ResponseType.ACCEPT
            );
            var filter = new Gtk.FileFilter ();
            filter.set_name ("Archive files");
            filter.add_pattern ("*.7z");
            filter.add_pattern ("*.zip");
            filter.add_pattern ("*.rar");
            dialog.add_filter (filter);
            if (dialog.run () == Gtk.ResponseType.ACCEPT) {
                ae_archive_path = dialog.get_filename ();
                ae_archive_entry.set_text (ae_archive_path);
                append_log ("[SELECT] After Effects archive: " + ae_archive_path);
            }
            dialog.destroy ();
        }

        private void on_select_msxml3 () {
            var dialog = new Gtk.FileChooserDialog (
                "Select msxml3.dll",
                this,
                Gtk.FileChooserAction.OPEN,
                "_Cancel", Gtk.ResponseType.CANCEL,
                "_Open", Gtk.ResponseType.ACCEPT
            );
            var filter = new Gtk.FileFilter ();
            filter.set_name ("DLL files");
            filter.add_pattern ("*.dll");
            dialog.add_filter (filter);
            if (dialog.run () == Gtk.ResponseType.ACCEPT) {
                msxml3_path = dialog.get_filename ();
                xml3_entry.set_text (msxml3_path);
                append_log ("[SELECT] msxml3.dll: " + msxml3_path);
            }
            dialog.destroy ();
        }

        private void on_select_msxml3r () {
            var dialog = new Gtk.FileChooserDialog (
                "Select msxml3r.dll",
                this,
                Gtk.FileChooserAction.OPEN,
                "_Cancel", Gtk.ResponseType.CANCEL,
                "_Open", Gtk.ResponseType.ACCEPT
            );
            var filter = new Gtk.FileFilter ();
            filter.set_name ("DLL files");
            filter.add_pattern ("*.dll");
            dialog.add_filter (filter);
            if (dialog.run () == Gtk.ResponseType.ACCEPT) {
                msxml3r_path = dialog.get_filename ();
                xml3r_entry.set_text (msxml3r_path);
                append_log ("[SELECT] msxml3r.dll: " + msxml3r_path);
            }
            dialog.destroy ();
        }

        private void on_cancel_clicked () {
            cancelled = true;
            append_log ("[SETUP] Cancelling installation...");
            Utils.kill_active_subprocesses (Utils.get_executable_dir ());
            if (log_file != null) {
                log_file = null;
            }
            this.close ();
        }

        private void on_install_clicked () {
            install_dir = install_dir_entry.get_text ().strip ();
            if (install_dir == "") {
                append_log ("[ERROR] Please select an installation directory.");
                return;
            }
            if (ae_archive_path == null || ae_archive_path == "") {
                append_log ("[ERROR] Please select the After Effects archive first.");
                return;
            }
            if (msxml3_path == null || msxml3_path == "") {
                append_log ("[ERROR] Please select msxml3.dll first.");
                return;
            }
            if (msxml3r_path == null || msxml3r_path == "") {
                append_log ("[ERROR] Please select msxml3r.dll first.");
                return;
            }

            cancelled = false;
            
            // Hide top bar cancel button (we show the cancel button in the middle stack bottom)
            cancel_button.set_visible (false);
            
            wizard_stack.set_visible_child_name ("page4");
            top_title_label.set_text ("Install AeNux (0%)");

            append_log ("[SETUP] Starting installation...");

            string target_dir = install_dir;
            string ae_path = ae_archive_path;
            string xml3 = msxml3_path;
            string xml3r = msxml3r_path;

            new Thread<int> ("installer", () => {
                run_installation (target_dir, ae_path, xml3, xml3r);
                return 0;
            });
        }

        private int run_installation (string base_dir, string ae_archive, string xml3, string xml3r) {
            DirUtils.create_with_parents (base_dir, 0755);
            Utils.set_config_value ("aenux_path", Path.build_filename (base_dir, "AfterEffects"));

            // Initialize logging to file
            string log_path = Path.build_filename (base_dir, "install.log");
            log_file = FileStream.open (log_path, "w");
            if (log_file != null) {
                log_file.printf ("=== AeNux Installation Log ===\n");
            }

            if (cancelled) return 0;

            // 0. Install system packages via pkexec
            update_progress (0.05, "Installing extraction tools, Wine deps & OpenCL drivers (requires authentication)...");
            append_log ("[SETUP] Running package manager to install dependencies...");

            string package_script =
                "apt-get update -qq || true; " +
                "apt-get install -y p7zip-full unzip tar curl cabextract; " +
                "apt-get install -y unrar || apt-get install -y unrar-free || true; " +
                "echo '[SETUP] Installing Wine runtime libraries (FreeType, fonts, gnutls)...'; " +
                "dpkg --add-architecture i386 || true; " +
                "apt-get update -qq || true; " +
                "apt-get install -y libfreetype6 libfreetype6:i386 || true; " +
                "apt-get install -y libgnutls30 libgnutls30:i386 || true; " +
                "apt-get install -y libgstreamer1.0-0 libgstreamer-plugins-base1.0-0 || true; " +
                "if lspci | grep -qi nvidia; then " +
                "  echo '[SETUP] NVIDIA GPU detected. Installing NVIDIA OpenCL support...'; " +
                "  apt-get install -y ocl-icd-opencl-dev nvidia-opencl-dev || true; " +
                "elif lspci | grep -qi amd || lspci | grep -qi radeon; then " +
                "  echo '[SETUP] AMD GPU detected. Installing Mesa OpenCL + RustiCL support...'; " +
                "  apt-get install -y ocl-icd-opencl-dev ocl-icd-libopencl1 mesa-opencl-icd || true; " +
                "elif lspci | grep -qi intel; then " +
                "  echo '[SETUP] Intel GPU detected. Installing Intel OpenCL support...'; " +
                "  apt-get install -y ocl-icd-opencl-dev intel-opencl-icd || true; " +
                "else " +
                "  echo '[SETUP] Generic GPU. Installing generic OpenCL loader...'; " +
                "  apt-get install -y ocl-icd-opencl-dev ocl-icd-libopencl1 || true; " +
                "fi";

            Utils.run_command_stream (
                {"pkexec", "bash", "-c", package_script},
                (line) => { append_log (line); }
            );

            // Temp directory for downloads
            string temp_dir = Path.build_filename (base_dir, "TEMP");
            DirUtils.create_with_parents (temp_dir, 0755);

            // --- Locate or install 7-Zip for extraction ---
            if (cancelled) return 0;
            update_progress (0.06, "Preparing 7-Zip extraction tool...");
            string sevenzip_bin = Path.build_filename (temp_dir, "7zz");
            if (!FileUtils.test (sevenzip_bin, FileTest.EXISTS)) {
                append_log ("[SETUP] Downloading standalone 7-Zip for Linux from 7-zip.org...");
                string sevenz_tar = Path.build_filename (temp_dir, "7z-linux.tar.xz");
                Utils.download_file_with_progress ("https://www.7-zip.org/a/7z2301-linux-x64.tar.xz", sevenz_tar, (fraction, msg) => {
                    update_progress (0.05 + fraction * 0.03, "Preparing standalone 7-Zip tool...");
                    append_log (msg);
                });
                string? out7z, err7z;
                Utils.run_command ({"tar", "-xf", sevenz_tar, "-C", temp_dir, "7zz"}, null, null, out out7z, out err7z);
                FileUtils.chmod (sevenzip_bin, 0755);
            }
            if (!FileUtils.test (sevenzip_bin, FileTest.EXISTS)) {
                string? sys_7zz = GLib.Environment.find_program_in_path ("7zz");
                string? sys_7z = GLib.Environment.find_program_in_path ("7z");
                sevenzip_bin = sys_7zz ?? sys_7z ?? "7z";
            }
            append_log ("[SETUP] Standalone 7-Zip (7zz) is ready and will be used for all archive extractions.");

            // --- Downloads ---
            if (cancelled) return 0;
            update_progress (0.09, "Downloading Wine, Gecko, Winetricks, and Redists...");
            append_log ("[DOWNLOAD] Retrieving Wine, Gecko, Winetricks, and Redists...");

            string vc64 = Path.build_filename (temp_dir, "vc_redist.x64.exe");
            string vc86 = Path.build_filename (temp_dir, "vc_redist.x86.exe");
            string wine_archive = Path.build_filename (temp_dir, "wine-proton-exp-11.0-amd64.tar.xz");
            string gecko = Path.build_filename (temp_dir, "wine-gecko-2.47.4-x86_64.msi");
            string winetricks = Path.build_filename (temp_dir, "winetricks");

            if (cancelled) return 0;
            if (!FileUtils.test (vc64, FileTest.EXISTS)) {
                append_log ("[DOWNLOAD] Source: https://aka.ms/vs/17/release/vc_redist.x64.exe");
                append_log ("[DOWNLOAD] Destination: " + vc64);
                Utils.download_file_with_progress ("https://aka.ms/vs/17/release/vc_redist.x64.exe", vc64, (fraction, msg) => {
                    update_progress (0.10 + fraction * 0.04, "Downloading VC++ Redistributable x64...");
                    append_log (msg);
                });
                append_log ("[DOWNLOAD] Completed vc_redist.x64.exe");
            }
            if (cancelled) return 0;
            if (!FileUtils.test (vc86, FileTest.EXISTS)) {
                append_log ("[DOWNLOAD] Source: https://aka.ms/vs/17/release/vc_redist.x86.exe");
                append_log ("[DOWNLOAD] Destination: " + vc86);
                Utils.download_file_with_progress ("https://aka.ms/vs/17/release/vc_redist.x86.exe", vc86, (fraction, msg) => {
                    update_progress (0.14 + fraction * 0.04, "Downloading VC++ Redistributable x86...");
                    append_log (msg);
                });
                append_log ("[DOWNLOAD] Completed vc_redist.x86.exe");
            }
            if (cancelled) return 0;
            if (!FileUtils.test (wine_archive, FileTest.EXISTS)) {
                append_log ("[DOWNLOAD] Source: https://github.com/Kron4ek/Wine-Builds/releases/download/proton-exp-11.0/wine-proton-exp-11.0-amd64.tar.xz");
                append_log ("[DOWNLOAD] Destination: " + wine_archive);
                Utils.download_file_with_progress ("https://github.com/Kron4ek/Wine-Builds/releases/download/proton-exp-11.0/wine-proton-exp-11.0-amd64.tar.xz", wine_archive, (fraction, msg) => {
                    update_progress (0.18 + fraction * 0.12, "Downloading Wine Proton Experimental 11.0 (Kron4ek)...");
                    append_log (msg);
                });
                append_log ("[DOWNLOAD] Completed Wine Proton Experimental 11.0 archive");
            }
            if (cancelled) return 0;
            if (!FileUtils.test (gecko, FileTest.EXISTS)) {
                append_log ("[DOWNLOAD] Source: https://dl.winehq.org/wine/wine-gecko/2.47.4/wine-gecko-2.47.4-x86_64.msi");
                append_log ("[DOWNLOAD] Destination: " + gecko);
                Utils.download_file_with_progress ("https://dl.winehq.org/wine/wine-gecko/2.47.4/wine-gecko-2.47.4-x86_64.msi", gecko, (fraction, msg) => {
                    update_progress (0.30 + fraction * 0.04, "Downloading Wine Gecko...");
                    append_log (msg);
                });
                append_log ("[DOWNLOAD] Completed Wine Gecko MSI");
            }
            if (cancelled) return 0;
            if (!FileUtils.test (winetricks, FileTest.EXISTS)) {
                append_log ("[DOWNLOAD] Source: https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks");
                append_log ("[DOWNLOAD] Destination: " + winetricks);
                Utils.download_file_with_progress ("https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks", winetricks, (fraction, msg) => {
                    update_progress (0.34 + fraction * 0.01, "Downloading Winetricks...");
                    append_log (msg);
                });
                append_log ("[DOWNLOAD] Completed Winetricks script");
            }

            // 2. Extract After Effects
            if (cancelled) return 0;
            update_progress (0.36, "Extracting After Effects archive...");
            append_log ("[EXTRACT] Extracting After Effects archive...");
            string ae_dir = Path.build_filename (base_dir, "AfterEffects");
            DirUtils.create_with_parents (ae_dir, 0755);
            if (!Utils.run_command_stream ({sevenzip_bin, "x", ae_archive, "-o" + ae_dir, "-y"}, (msg) => {
                append_log ("[EXTRACT-AE] " + msg);
            })) {
                append_log ("[ERROR] Failed to extract After Effects archive. Please check the file and try again.");
                return 0;
            }

            // 3. Extract Wine
            if (cancelled) return 0;
            update_progress (0.50, "Extracting Wine Proton Experimental 11.0 (Kron4ek)...");
            append_log ("[EXTRACT] Extracting Kron4ek Wine Proton Experimental 11.0...");
            string wine_dir = Path.build_filename (base_dir, "wine");
            DirUtils.create_with_parents (wine_dir, 0755);
            if (!Utils.run_command_stream ({"tar", "--strip-components=1", "-xvf", wine_archive, "-C", wine_dir}, (msg) => {
                append_log ("[EXTRACT-WINE] " + msg);
            })) {
                append_log ("[ERROR] Failed to extract Wine archive. Please check the file and try again.");
                return 0;
            }

            // 4. Install Winetricks
            if (cancelled) return 0;
            update_progress (0.60, "Copying winetricks tool...");
            append_log ("[SETUP] Installing Winetricks...");
            string wt_dest = Path.build_filename (wine_dir, "bin", "winetricks");
            FileUtils.chmod (winetricks, 0755);
            File.new_for_path (winetricks).copy (File.new_for_path (wt_dest), FileCopyFlags.OVERWRITE, null, null);
            FileUtils.chmod (wt_dest, 0755);
            append_log ("[SETUP] Winetricks installed to " + wt_dest);

            // 5. Wineprefix Init
            if (cancelled) return 0;
            update_progress (0.70, "Initializing Wine prefix...");
            append_log ("[WINE] Constructing wine prefix environment...");
            string prefix_dir = Path.build_filename (base_dir, "Wineprefix");
            DirUtils.create_with_parents (prefix_dir, 0755);
            string wine_bin = Path.build_filename (wine_dir, "bin", "wine");
            string wineserver_bin = Path.build_filename (wine_dir, "bin", "wineserver");

            string[] env = Utils.get_wine_env (wine_dir, prefix_dir);
            string[] env_silent = env;
            env_silent = Environ.set_variable (env_silent, "WINEDLLOVERRIDES",
                "winemenubuilder.exe=d;mscoree=d;mshtml=d");
            
            // Enable warnings/errors logging for wineboot to not be silent
            env_silent = Environ.set_variable (env_silent, "WINEDEBUG", "+warn,+err");

            append_log ("[WINE] Running wineboot -u (timeout 60s)...");
            Utils.run_command_stream ({"timeout", "60", wine_bin, "wineboot", "-u"}, (line) => {
                append_log ("[WINEBOOT] " + line);
            }, env_silent);

            // Kill wineserver
            string? o_ws, e_ws;
            Utils.run_command ({"timeout", "5", wineserver_bin, "-k"}, env_silent, null, out o_ws, out e_ws);
            GLib.Thread.usleep (500000); // 0.5s settle
            append_log ("[WINE] Wineprefix initialized.");

            // 6. Dependencies — gecko, vcredist, winetricks verbs
            if (cancelled) return 0;
            update_progress (0.80, "Installing VC++ Redists, Wine Gecko, DXVK/VKD3D...");

            string[] env_install = env;
            env_install = Environ.set_variable (env_install, "WINEDLLOVERRIDES",
                "winemenubuilder.exe=d;mscoree=d");

            append_log ("[WINE] Installing gecko...");
            Utils.run_command_stream ({"timeout", "120", wine_bin, "msiexec",
                "/i", gecko, "/quiet", "/norestart"}, (line) => {
                append_log ("[MSIEXEC] " + line);
            }, env_install);

            if (cancelled) return 0;
            append_log ("[WINE] Installing vc_redist x64...");
            Utils.run_command_stream ({"timeout", "120", wine_bin, vc64,
                "/install", "/quiet", "/norestart"}, (line) => {
                append_log ("[VCREDIST-X64] " + line);
            }, env_install);

            if (cancelled) return 0;
            append_log ("[WINE] Installing vc_redist x86...");
            Utils.run_command_stream ({"timeout", "120", wine_bin, vc86,
                "/install", "/quiet", "/norestart"}, (line) => {
                append_log ("[VCREDIST-X86] " + line);
            }, env_install);

            // Winetricks verbs
            string[] verbs = {"dxvk", "vkd3d", "corefonts", "gdiplus", "fontsmooth=rgb"};
            foreach (var verb in verbs) {
                if (cancelled) return 0;
                append_log ("[WINE] Winetricks install " + verb);
                Utils.run_command_stream ({"timeout", "180", wt_dest, "--unattended", verb}, (line) => {
                    append_log ("[WINETRICKS-" + verb.up () + "] " + line);
                }, env_install);
            }

            // 7. DLL overrides & registry configuration
            if (cancelled) return 0;
            update_progress (0.95, "Copying DLLs and configuring registry...");
            append_log ("[SETUP] Copying msxml3.dll and msxml3r.dll...");
            string system32 = Path.build_filename (prefix_dir, "drive_c", "windows", "system32");

            try {
                File.new_for_path (xml3).copy (File.new_for_path (Path.build_filename (system32, "msxml3.dll")), FileCopyFlags.OVERWRITE, null, null);
                File.new_for_path (xml3r).copy (File.new_for_path (Path.build_filename (system32, "msxml3r.dll")), FileCopyFlags.OVERWRITE, null, null);
            } catch (Error err) {
                append_log ("[ERROR] Failed to copy DLLs: " + err.message);
            }

            string? o, e;
            append_log ("[SETUP] Registering msxml3 DLL override...");
            Utils.run_command ({wine_bin, "reg", "add", "HKCU\\Software\\Wine\\DllOverrides", "/v", "msxml3", "/d", "native,builtin", "/f"}, env, null, out o, out e);
            append_log ("[SETUP] Registering msxml3r DLL override...");
            Utils.run_command ({wine_bin, "reg", "add", "HKCU\\Software\\Wine\\DllOverrides", "/v", "msxml3r", "/d", "native,builtin", "/f"}, env, null, out o, out e);

            append_log ("[SETUP] Setting Wine Windows version to Windows 10...");
            Utils.run_command ({wine_bin, "reg", "add", "HKCU\\Software\\Wine", "/v", "Version", "/d", "win10", "/f"}, env, null, out o, out e);

            append_log ("[SETUP] Applying dark theme registry settings...");
            Utils.set_theme_registry (wine_dir, prefix_dir);

            append_log ("[SETUP] Enabling CEP extension debug mode...");
            for (int v = 7; v <= 12; v++) {
                Utils.run_command ({wine_bin, "reg", "add", "HKCU\\Software\\Adobe\\CSXS." + v.to_string (), "/v", "PlayerDebugMode", "/d", "1", "/f"}, env, null, out o, out e);
            }

            // 8. Save config
            if (cancelled) return 0;
            update_progress (0.99, "Saving configuration...");
            Utils.set_config_value ("wine_path", wine_dir);
            Utils.set_config_value ("wineprefix", prefix_dir);
            Utils.set_config_value ("aenux_path", ae_dir);

            update_progress (1.0, "Installation complete!");
            append_log ("[SETUP] Installation completed successfully!");
            append_log ("[SETUP] Wine path: " + wine_dir);
            append_log ("[SETUP] Wine prefix: " + prefix_dir);
            append_log ("[SETUP] After Effects: " + ae_dir);

            if (log_file != null) {
                log_file = null;
            }

            Idle.add (() => {
                var d = new MessageDialog (
                    this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.OK,
                    "Installation complete!\n\nYou can now launch After Effects from the AeNux Runner."
                );
                d.run ();
                d.destroy ();
                this.close ();
                return false;
            });

            return 0;
        }

        private void append_log (string message) {
            stdout.printf ("%s\n", message);
            if (log_file != null) {
                log_file.printf ("%s\n", message);
                log_file.flush ();
            }
            Idle.add (() => {
                if (!this.get_visible ()) {
                    return false;
                }
                Gtk.TextIter end;
                log_buffer.get_end_iter (out end);
                log_buffer.insert (ref end, message + "\n", -1);
                var adj = log_scroll.get_vadjustment ();
                if (adj != null) {
                    adj.set_value (adj.get_upper () - adj.get_page_size ());
                }
                return false;
            });
        }

        private void update_progress (double fraction, string status) {
            Idle.add (() => {
                if (!this.get_visible ()) {
                    return false;
                }
                progress_bar.set_fraction (fraction.clamp (0.0, 1.0));
                
                string title_percentage = "Install AeNux (%.0f%%)".printf (fraction * 100);
                top_title_label.set_text (title_percentage);
                return false;
            });
        }
    }
}

