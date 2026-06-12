/*
 * Utils.vala
 * Common utility methods for AeNux.
 */

using GLib;

namespace AeNux {
    public class Utils : Object {
        [CCode (cname = "waitpid", cheader_filename = "sys/wait.h")]
        private extern static int wait_pid (int pid, out int status, int options);

        [CCode (cname = "kill", cheader_filename = "signal.h")]
        private extern static int posix_kill (int pid, int sig);

        [CCode (cname = "fcntl", cheader_filename = "fcntl.h")]
        private extern static int fcntl (int fd, int cmd, int arg = 0);
        private const int F_GETFL = 3;
        private const int F_SETFL = 4;
        private const int O_NONBLOCK = 2048;

        public static Pid active_pid = 0;
        public static string custom_7z_path = "";
        public delegate void StreamCallback (string message);

        public static void kill_active_subprocesses (string base_dir) {
            if (active_pid > 0) {
                posix_kill ((int) active_pid, 9); // SIGKILL
                active_pid = 0;
            }

            // SIGKILL all Wine/Winetricks/curl processes
            string? o, e;
            run_command ({"pkill", "-9", "-f", "curl"}, null, null, out o, out e);
            run_command ({"pkill", "-9", "-f", "winetricks"}, null, null, out o, out e);
            run_command ({"pkill", "-9", "-f", "AfterFX.exe"}, null, null, out o, out e);
            run_command ({"pkill", "-9", "-f", "wine"}, null, null, out o, out e);
            run_command ({"pkill", "-9", "-f", "wineserver"}, null, null, out o, out e);
        }

        /*
         * Nuclear kill: terminates every Wine-related process with SIGKILL.
         * Call this when you need a guaranteed clean slate.
         */
        public static void nuke_all_wine_processes (string wine_path, string wineprefix) {
            string? o, e;

            // 1. Ask wineserver to shut down gracefully first
            string wineserver_bin = Path.build_filename (wine_path, "bin", "wineserver");
            if (FileUtils.test (wineserver_bin, FileTest.EXISTS)) {
                string[] env = get_wine_env (wine_path, wineprefix);
                run_command ({wineserver_bin, "-k"}, env, null, out o, out e);
                GLib.Thread.usleep (300000); // give it 0.3s to shut down
            }

            // 2. SIGKILL every wine-related process by name pattern
            string[] patterns = {
                "AfterFX.exe",
                "AfterFX",
                "wineserver",
                "wine-preloader",
                "wine64-preloader",
                "services.exe",
                "explorer.exe",
                "plugplay.exe",
                "svchost.exe",
                "rpcss.exe",
                "winemenubuilder",
                "wine"
            };

            foreach (var pattern in patterns) {
                run_command ({"pkill", "-9", "-f", pattern}, null, null, out o, out e);
            }

            // 3. Final wait to reap zombies
            GLib.Thread.usleep (200000); // 0.2s
        }

        public static string get_config_path () {
            return Path.build_filename (get_executable_dir (), "settings.json");
        }

        public static string get_executable_dir () {
            try {
                string exe_path = FileUtils.read_link ("/proc/self/exe");
                return Path.get_dirname (exe_path);
            } catch (Error e) {
                return Environment.get_current_dir ();
            }
        }

        public static string? get_config_value (string key) {
            string path = get_config_path ();
            if (!FileUtils.test (path, FileTest.EXISTS)) {
                return null;
            }
            try {
                string content;
                FileUtils.get_contents (path, out content);
                var regex = new Regex ("\"" + Regex.escape_string (key) + "\"\\s*:\\s*\"([^\"]*)\"");
                MatchInfo match;
                if (regex.match (content, 0, out match)) {
                    return match.fetch (1);
                }
            } catch (Error e) {
                // ignore
            }
            return null;
        }

        public static bool set_config_value (string key, string val) {
            string path = get_config_path ();
            string content = "{}";
            if (FileUtils.test (path, FileTest.EXISTS)) {
                try {
                    FileUtils.get_contents (path, out content);
                } catch (Error e) {
                    content = "{}";
                }
            }

            content = content.strip ();
            if (!content.has_prefix ("{")) {
                content = "{\n}";
            }

            try {
                var regex = new Regex ("\"" + Regex.escape_string (key) + "\"\\s*:\\s*\"[^\"]*\"");
                if (regex.match (content)) {
                    string replacement = "\"%s\": \"%s\"".printf (key, val);
                    content = regex.replace_literal (content, -1, 0, replacement);
                } else {
                    int last_brace = content.last_index_of_char ('}');
                    if (last_brace != -1) {
                        string prefix = content.substring (0, last_brace).strip ();
                        if (prefix == "{") {
                            content = "{\n  \"%s\": \"%s\"\n}".printf (key, val);
                        } else {
                            if (prefix.has_suffix (",")) {
                                content = "%s\n  \"%s\": \"%s\"\n}".printf (prefix, key, val);
                            } else {
                                content = "%s,\n  \"%s\": \"%s\"\n}".printf (prefix, key, val);
                            }
                        }
                    } else {
                        content = "{\n  \"%s\": \"%s\"\n}".printf (key, val);
                    }
                }
                FileUtils.set_contents (path, content);
                return true;
            } catch (Error e) {
                stderr.printf ("Error saving JSON config: %s\n", e.message);
                return false;
            }
        }

        public static bool run_command (string[] args, string[]? env = null, string? cwd = null, out string? stdout_res = null, out string? stderr_res = null) {
            stdout_res = "";
            stderr_res = "";
            try {
                Pid child_pid;
                int stdout_fd, stderr_fd;
                Process.spawn_async_with_pipes (
                    cwd,
                    args,
                    env,
                    SpawnFlags.SEARCH_PATH | SpawnFlags.DO_NOT_REAP_CHILD,
                    null,
                    out child_pid,
                    null,
                    out stdout_fd,
                    out stderr_fd
                );

                active_pid = child_pid;

                // Set non-blocking
                int out_flags = fcntl (stdout_fd, F_GETFL, 0);
                fcntl (stdout_fd, F_SETFL, out_flags | O_NONBLOCK);
                int err_flags = fcntl (stderr_fd, F_GETFL, 0);
                fcntl (stderr_fd, F_SETFL, err_flags | O_NONBLOCK);

                var stdout_stream = new DataInputStream (new UnixInputStream (stdout_fd, true));
                var stderr_stream = new DataInputStream (new UnixInputStream (stderr_fd, true));

                StringBuilder stdout_sb = new StringBuilder ();
                StringBuilder stderr_sb = new StringBuilder ();
                bool out_eof = false;
                bool err_eof = false;
                int status = 0;

                while (!out_eof || !err_eof) {
                    if (!out_eof) {
                        try {
                            size_t len;
                            string? line = stdout_stream.read_line (out len, null);
                            if (line != null) {
                                stdout_sb.append (line + "\n");
                            } else {
                                out_eof = true;
                            }
                        } catch (Error e) {
                            if (e is IOError.WOULD_BLOCK) {
                                int res = wait_pid ((int) child_pid, out status, 1); // WNOHANG = 1
                                if (res == (int) child_pid || res == -1) {
                                    out_eof = true;
                                }
                            } else {
                                out_eof = true;
                            }
                        }
                    }

                    if (!err_eof) {
                        try {
                            size_t len;
                            string? line = stderr_stream.read_line (out len, null);
                            if (line != null) {
                                stderr_sb.append (line + "\n");
                            } else {
                                err_eof = true;
                            }
                        } catch (Error e) {
                            if (e is IOError.WOULD_BLOCK) {
                                int res = wait_pid ((int) child_pid, out status, 1);
                                if (res == (int) child_pid || res == -1) {
                                    err_eof = true;
                                }
                            } else {
                                err_eof = true;
                            }
                        }
                    }

                    if (!out_eof || !err_eof) {
                        GLib.Thread.usleep (10000); // 10ms
                    }
                }

                wait_pid ((int) child_pid, out status, 0);
                Process.close_pid (child_pid);
                active_pid = 0;

                stdout_res = stdout_sb.str;
                stderr_res = stderr_sb.str;
                return status == 0;
            } catch (Error e) {
                stderr_res = e.message;
                return false;
            }
        }

        public static bool run_command_stream (string[] args, StreamCallback cb, string[]? env = null, string? cwd = null) {
            try {
                var shell_cmd = new StringBuilder ();
                foreach (var arg in args) {
                    shell_cmd.append ("\"" + arg.replace ("\"", "\\\"") + "\" ");
                }
                shell_cmd.append (" 2>&1");

                string[] argv = {"bash", "-c", shell_cmd.str};

                Pid child_pid;
                int stdout_fd;
                Process.spawn_async_with_pipes (
                    cwd,
                    argv,
                    env,
                    SpawnFlags.SEARCH_PATH | SpawnFlags.DO_NOT_REAP_CHILD,
                    null,
                    out child_pid,
                    null,
                    out stdout_fd,
                    null
                );

                active_pid = child_pid;

                // Set non-blocking
                int flags = fcntl (stdout_fd, F_GETFL, 0);
                fcntl (stdout_fd, F_SETFL, flags | O_NONBLOCK);

                var stream = new DataInputStream (new UnixInputStream (stdout_fd, true));
                int status = 0;
                bool stream_eof = false;

                while (!stream_eof) {
                    try {
                        size_t len;
                        string? line = stream.read_line (out len, null);
                        if (line != null) {
                            cb (line.strip ());
                        } else {
                            stream_eof = true;
                        }
                    } catch (Error e) {
                        if (e is IOError.WOULD_BLOCK) {
                            int res = wait_pid ((int) child_pid, out status, 1); // WNOHANG = 1
                            if (res == (int) child_pid || res == -1) {
                                stream_eof = true;
                            } else {
                                GLib.Thread.usleep (10000); // 10ms
                            }
                        } else {
                            cb ("[ERROR] " + e.message);
                            stream_eof = true;
                        }
                    }
                }

                wait_pid ((int) child_pid, out status, 0);
                Process.close_pid (child_pid);
                active_pid = 0;

                return status == 0;
            } catch (Error e) {
                cb ("[ERROR] " + e.message);
                return false;
            }
        }

        /*
         * Build environment for running Wine (Kron4ek builds).
         * wine_path = root of extracted Kron4ek archive (contains bin/, lib/, share/)
         * wineprefix = path to the Wine prefix directory
         */
        public static string[] get_wine_env (string wine_path, string wineprefix) {
            string[] env = Environ.get ();
            env = Environ.set_variable (env, "WINEPREFIX", wineprefix);
            env = Environ.set_variable (env, "WINEDEBUG", "-all");

            // Set Windows version to Win10 to satisfy After Effects requirements
            env = Environ.set_variable (env, "WINEARCH", "win64");

            // Auto-enable RustiCL for AMD/Intel GPUs (Mesa OpenCL)
            string? rusticl_env = Environment.get_variable ("RUSTICL_ENABLE");
            if (rusticl_env == null) {
                string? o, e;
                if (run_command ({"lspci"}, null, null, out o, out e)) {
                    string o_down = o.down ();
                    if (o_down.contains ("amd") || o_down.contains ("radeon")) {
                        env = Environ.set_variable (env, "RUSTICL_ENABLE", "radeonsi");
                    } else if (o_down.contains ("intel")) {
                        env = Environ.set_variable (env, "RUSTICL_ENABLE", "iris");
                    }
                }
            }

            // --- Display / Wayland setup ---
            // Wine 9.0+ has native Wayland driver. On Wayland sessions, prefer it
            // over XWayland to avoid "X connection broken" crashes.
            string? wayland_display = Environment.get_variable ("WAYLAND_DISPLAY");
            string? xdg_runtime = Environment.get_variable ("XDG_RUNTIME_DIR");
            string? session_type = Environment.get_variable ("XDG_SESSION_TYPE");
            string? display = Environment.get_variable ("DISPLAY");

            if (xdg_runtime != null && xdg_runtime != "") {
                env = Environ.set_variable (env, "XDG_RUNTIME_DIR", xdg_runtime);
            }

            bool is_wayland = (session_type != null && session_type.down () == "wayland") ||
                              (wayland_display != null && wayland_display != "");

            if (is_wayland && wayland_display != null && wayland_display != "") {
                // Forward Wayland socket so Wine can use its native Wayland driver
                env = Environ.set_variable (env, "WAYLAND_DISPLAY", wayland_display);
                // Still forward DISPLAY for any X11 fallback (e.g. XWayland)
                if (display != null && display != "") {
                    env = Environ.set_variable (env, "DISPLAY", display);
                }
            } else if (display != null && display != "") {
                // Pure X11 session — just forward DISPLAY
                env = Environ.set_variable (env, "DISPLAY", display);
            }

            // Kron4ek Wine bin is at wine_path/bin (not files/bin like GE-Proton)
            string wine_bin_path = Path.build_filename (wine_path, "bin");
            string? current_path = Environment.get_variable ("PATH");
            if (current_path != null) {
                env = Environ.set_variable (env, "PATH", wine_bin_path + ":" + current_path);
            } else {
                env = Environ.set_variable (env, "PATH", wine_bin_path);
            }
            return env;
        }


        public static bool kill_wine_processes (string wine_path, string wineprefix) {
            nuke_all_wine_processes (wine_path, wineprefix);
            return true;
        }

        public static void set_theme_registry (string wine_path, string wineprefix) {
            // Kron4ek: wine binary at wine_path/bin/wine
            string wine_bin = Path.build_filename (wine_path, "bin", "wine");
            if (!FileUtils.test (wine_bin, FileTest.EXISTS)) {
                return;
            }

            string[] env = get_wine_env (wine_path, wineprefix);
            string[] keys = {
                "ActiveBorder", "ActiveTitle", "AppWorkSpace", "Background",
                "ButtonAlternativeFace", "ButtonDkShadow", "ButtonFace", "ButtonHilight",
                "ButtonLight", "ButtonShadow", "ButtonText", "GradientActiveTitle",
                "GradientInactiveTitle", "GrayText", "Hilight", "HilightText",
                "InactiveBorder", "InactiveTitle", "InactiveTitleText", "InfoText",
                "InfoWindow", "Menu", "MenuBar", "MenuHilight", "MenuText",
                "Scrollbar", "TitleText", "Window", "WindowFrame", "WindowText"
            };

            string[] values = {
                "49 54 58", "49 54 58", "60 64 72", "49 54 58",
                "60 64 72", "30 33 36", "49 54 58", "119 126 140",
                "60 64 72", "40 43 47", "219 220 222", "49 54 58",
                "49 54 58", "100 104 110", "119 126 140", "255 255 255",
                "49 54 58", "49 54 58", "219 220 222", "180 185 190",
                "49 54 58", "40 43 47", "40 43 47", "119 126 140", "219 220 222",
                "60 64 72", "219 220 222", "35 38 41", "49 54 58", "219 220 222"
            };

            for (int i = 0; i < keys.length; i++) {
                string key = keys[i];
                string val = values[i];
                string? o, e;
                run_command ({wine_bin, "reg", "add", "HKCU\\Control Panel\\Colors", "/v", key, "/d", val, "/f"}, env, null, out o, out e);
            }
        }

        public static void create_shortcuts (string wine_path, string wineprefix, string aenux_path) {
            try {
                string users_dir = Path.build_filename (wineprefix, "drive_c", "users");
                if (!FileUtils.test (users_dir, FileTest.IS_DIR)) {
                    return;
                }

                Dir dir = Dir.open (users_dir);
                string? name;
                while ((name = dir.read_name ()) != null) {
                    if (name == "." || name == "..") continue;
                    
                    string fav_path = Path.build_filename (users_dir, name, "Favorites");
                    if (FileUtils.test (fav_path, FileTest.IS_DIR)) {
                        string home_dir = Environment.get_home_dir ();
                        string[] folders = {"Documents", "Downloads", "Pictures", "Videos", "Music"};
                        foreach (var folder in folders) {
                            string link_path = Path.build_filename (fav_path, folder);
                            if (FileUtils.test (link_path, FileTest.EXISTS)) {
                                FileUtils.remove (link_path);
                            }
                            string target = Path.build_filename (home_dir, folder);
                            if (FileUtils.test (target, FileTest.IS_DIR)) {
                                File.new_for_path (link_path).make_symbolic_link (target);
                            }
                        }

                        if (aenux_path != "" && FileUtils.test (aenux_path, FileTest.IS_DIR)) {
                            string aenux_link = Path.build_filename (fav_path, "AeNux");
                            if (FileUtils.test (aenux_link, FileTest.EXISTS)) {
                                FileUtils.remove (aenux_link);
                            }
                            File.new_for_path (aenux_link).make_symbolic_link (aenux_path);
                        }
                    }
                }
                kill_wine_processes (wine_path, wineprefix);
            } catch (Error e) {
                stderr.printf ("Shortcut creation failed: %s\n", e.message);
            }
        }

        public static bool download_file (string url, string filepath) {
            string? o, e;
            return run_command ({"curl", "-L", "-o", filepath, url}, null, null, out o, out e);
        }

        public delegate void ProgressCallback (double fraction, string message);

        public static bool download_file_with_progress (string url, string filepath, ProgressCallback cb) {
            try {
                Pid child_pid;
                int stderr_fd;
                string[] argv = {"curl", "-L", "-o", filepath, url};
                Process.spawn_async_with_pipes (
                    null,
                    argv,
                    null,
                    SpawnFlags.SEARCH_PATH | SpawnFlags.DO_NOT_REAP_CHILD,
                    null,
                    out child_pid,
                    null,
                    null,
                    out stderr_fd
                );

                active_pid = child_pid;

                var dis = new DataInputStream (new UnixInputStream (stderr_fd, true));
                var sb = new StringBuilder ();
                
                try {
                    while (true) {
                        uint8 b = dis.read_byte (null);
                        if (b == 0) {
                            break;
                        }
                        char c = (char) b;
                        if (c == '\r' || c == '\n') {
                            string line = sb.str.strip ();
                            sb.assign ("");
                            
                            if (line == "" || line.has_prefix ("%") || line.has_prefix ("Dload") || line.has_prefix ("Time")) {
                                continue;
                            }
                            
                            line = line.replace ("\r", "").replace ("\n", "");

                            string[] parts = line.split_set (" \t", 0);
                            string[] words = {};
                            foreach (var part in parts) {
                                if (part != "") {
                                    words += part;
                                }
                            }

                            if (words.length >= 12) {
                                double pct = double.parse (words[0]);
                                string total_size = words[1];
                                string received_size = words[3];
                                string left_time = words[10];
                                string speed = words[11];

                                if (pct >= 0 && pct <= 100) {
                                    double fraction = pct / 100.0;
                                    string msg = "Downloading... %s%% (%s of %s) | Speed: %s | ETA: %s".printf (words[0], received_size, total_size, speed, left_time);
                                    cb (fraction, msg);
                                }
                            }
                        } else {
                            sb.append_c (c);
                        }
                    }
                } catch (Error e) {
                    // Stream closed or finished
                }

                int status = 0;
                wait_pid ((int) child_pid, out status, 0);
                Process.close_pid (child_pid);
                active_pid = 0;
                return true;
            } catch (Error e) {
                stderr.printf ("Download failed: %s\n", e.message);
                return false;
            }
        }

        public static bool copy_directory (string src, string dest) {
            string? o, e;
            return run_command ({"cp", "-R", src, dest}, null, null, out o, out e);
        }

        public static bool copy_file (string src, string dest) {
            string? o, e;
            return run_command ({"cp", src, dest}, null, null, out o, out e);
        }

        public static string get_user_applications_dir () {
            string data_dir = Environment.get_user_data_dir ();
            string app_dir = Path.build_filename (data_dir, "applications");
            if (!FileUtils.test (app_dir, FileTest.IS_DIR)) {
                DirUtils.create_with_parents (app_dir, 0755);
            }
            return app_dir;
        }

        public static void create_desktop_overrides () {
            string app_dir = get_user_applications_dir ();
            
            string config_content = 
                "[Desktop Entry]\n" +
                "Name=AeNux Config\n" +
                "Comment=Configure AeNux, Wineprefix, and Plugins\n" +
                "Exec=aenux_config\n" +
                "Icon=aenux-config\n" +
                "Type=Application\n" +
                "Terminal=false\n" +
                "Categories=Graphics;\n" +
                "X-GNOME-Menu-Folder=AeNux\n" +
                "Actions=CleanUninstall;\n\n" +
                "[Desktop Action CleanUninstall]\n" +
                "Name=Clean Uninstall AeNux\n" +
                "Exec=aenux_config --remove\n";
            string config_path = Path.build_filename (app_dir, "aenux.desktop");
            try {
                FileUtils.set_contents (config_path, config_content);
            } catch (Error err) {
                stderr.printf ("Failed to write desktop override: %s\n", err.message);
            }

            string runner_content =
                "[Desktop Entry]\n" +
                "Name=AeNux\n" +
                "Comment=Run After Effects on Linux\n" +
                "Exec=aenux\n" +
                "Icon=aenux\n" +
                "Type=Application\n" +
                "Terminal=false\n" +
                "Categories=Graphics;\n" +
                "X-GNOME-Menu-Folder=AeNux\n" +
                "Actions=Installer;\n\n" +
                "[Desktop Action Installer]\n" +
                "Name=AeNux Config\n" +
                "Exec=aenux_config\n";
            string runner_path = Path.build_filename (app_dir, "aenux-runner.desktop");
            try {
                FileUtils.set_contents (runner_path, runner_content);
            } catch (Error err) {
                stderr.printf ("Failed to write runner desktop shortcut: %s\n", err.message);
            }

            string? o, e;
            run_command ({"update-desktop-database", app_dir}, null, null, out o, out e);
        }

        public static void delete_desktop_overrides () {
            string app_dir = get_user_applications_dir ();
            string config_path = Path.build_filename (app_dir, "aenux.desktop");
            string runner_path = Path.build_filename (app_dir, "aenux-runner.desktop");

            if (FileUtils.test (config_path, FileTest.EXISTS)) {
                FileUtils.remove (config_path);
            }
            if (FileUtils.test (runner_path, FileTest.EXISTS)) {
                FileUtils.remove (runner_path);
            }

            string? o, e;
            run_command ({"update-desktop-database", app_dir}, null, null, out o, out e);
        }

        public static bool perform_clean_remove () {
            string? user_location = get_config_value ("user_location");
            if (user_location != null && user_location != "") {
                string? o, e;
                run_command ({"rm", "-rf", user_location}, null, null, out o, out e);
            }

            delete_desktop_overrides ();

            string config_file = get_config_path ();
            if (FileUtils.test (config_file, FileTest.EXISTS)) {
                FileUtils.remove (config_file);
            }

            string? o2, e2;
            run_command ({"pkexec", "dpkg", "-r", "aenux"}, null, null, out o2, out e2);
            return true;
        }

        public static void run_headless_runner () {
            string? wineprefix = get_config_value ("wineprefix");
            string? wine_path = get_config_value ("wine_path");
            string? aenux_path = get_config_value ("aenux_path");

            if (wineprefix == null || wine_path == null || aenux_path == null) return;

            // Kron4ek: wine binary at wine_path/bin/wine
            string wine_bin = Path.build_filename (wine_path, "bin", "wine");
            string afterfx_exe = Path.build_filename (aenux_path, "AfterFX.exe");

            if (!FileUtils.test (afterfx_exe, FileTest.EXISTS)) return;

            string[] env = get_wine_env (wine_path, wineprefix);
            string? o, e;

            run_command ({wine_bin, afterfx_exe}, env, null, out o, out e);
            
            kill_wine_processes (wine_path, wineprefix);
            run_command ({"pkill", "-f", "AfterFX.exe"}, null, null, out o, out e);
            run_command ({"pkill", "-f", "wine"}, null, null, out o, out e);
            run_command ({"pkill", "-f", "wineserver"}, null, null, out o, out e);
        }

        public static bool extract_archive (string archive_path, string dest_dir, StreamCallback? cb = null) {
            StreamCallback actual_cb = cb;
            if (actual_cb == null) {
                actual_cb = (msg) => {};
            }

            if (custom_7z_path != "" && FileUtils.test (custom_7z_path, FileTest.EXISTS)) {
                return run_command_stream ({custom_7z_path, "x", "-y", archive_path, "-o" + dest_dir}, actual_cb);
            }

            string ext = archive_path.down ();
            if (ext.has_suffix (".zip")) {
                return run_command_stream ({"unzip", "-o", archive_path, "-d", dest_dir}, actual_cb);
            } else if (ext.has_suffix (".tar.gz") || ext.has_suffix (".tgz")) {
                return run_command_stream ({"tar", "-xvf", archive_path, "-C", dest_dir}, actual_cb);
            } else if (ext.has_suffix (".tar.xz") || ext.has_suffix (".txz")) {
                return run_command_stream ({"tar", "-xvf", archive_path, "-C", dest_dir}, actual_cb);
            } else if (ext.has_suffix (".tar.bz2") || ext.has_suffix (".tbz2")) {
                return run_command_stream ({"tar", "-xvjf", archive_path, "-C", dest_dir}, actual_cb);
            } else if (ext.has_suffix (".tar")) {
                return run_command_stream ({"tar", "-xvf", archive_path, "-C", dest_dir}, actual_cb);
            } else if (ext.has_suffix (".7z")) {
                return run_command_stream ({"7z", "x", "-y", archive_path, "-o" + dest_dir}, actual_cb);
            } else if (ext.has_suffix (".rar")) {
                return run_command_stream ({"unrar", "x", "-y", archive_path, dest_dir}, actual_cb);
            } else {
                return run_command_stream ({"tar", "-xvf", archive_path, "-C", dest_dir}, actual_cb);
            }
        }
    }
}
