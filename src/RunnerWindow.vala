/*
 * RunnerWindow.vala
 * Small launcher window with log viewing, termination commands, and clipboard copying.
 */

using GLib;
using Gtk;

namespace AeNux {
    public class RunnerWindow : Window {
        private TextView log_view;
        private TextBuffer log_buffer;
        private ScrolledWindow scroll_win;
        private Button kill_btn;
        private Button copy_btn;
        private Pid child_pid = 0;

        public RunnerWindow (Gtk.Application app) {
            Object (application: app, title: "AeNux Runner");
            set_default_size (460, 320);
            window_position = WindowPosition.CENTER;
            resizable = false;

            // Header bar
            var header_bar = new HeaderBar ();
            header_bar.show_close_button = true;
            header_bar.title = "AeNux Runner";
            header_bar.subtitle = "Executing After Effects...";
            set_titlebar (header_bar);

            var main_box = new Box (Orientation.VERTICAL, 8);
            main_box.margin = 12;

            // Log Console
            scroll_win = new ScrolledWindow (null, null);
            scroll_win.shadow_type = ShadowType.IN;
            scroll_win.vexpand = true;

            log_view = new TextView ();
            log_view.editable = false;
            log_view.cursor_visible = false;
            log_view.left_margin = 8;
            log_view.right_margin = 8;
            log_view.top_margin = 8;
            log_view.bottom_margin = 8;
            log_view.get_style_context ().add_class ("console-log");
            log_buffer = log_view.buffer;
            scroll_win.add (log_view);
            main_box.pack_start (scroll_win, true, true, 0);

            // Controls Box
            var control_box = new Box (Orientation.HORIZONTAL, 12);

            copy_btn = new Button.with_label ("Copy Logs");
            copy_btn.clicked.connect (on_copy_logs_clicked);
            control_box.pack_start (copy_btn, true, true, 0);

            kill_btn = new Button.with_label ("Kill After Effects");
            kill_btn.get_style_context ().add_class ("destructive-action");
            kill_btn.clicked.connect (on_kill_clicked);
            control_box.pack_start (kill_btn, true, true, 0);

            main_box.pack_start (control_box, false, false, 0);

            add (main_box);

            // Close intercept event
            this.delete_event.connect (on_delete_event);

            // Auto-launch on map/show
            this.show.connect (on_window_shown);
        }

        private void append_log (string line) {
            Idle.add (() => {
                TextIter end;
                log_buffer.get_end_iter (out end);
                log_buffer.insert (ref end, line + "\n", -1);

                // Auto scroll to bottom
                var adj = scroll_win.vadjustment;
                adj.value = adj.upper - adj.page_size;
                return false;
            });
        }

        private void on_window_shown () {
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");
            string? aenux_path = Utils.get_config_value ("aenux_path");

            if (wineprefix == null || wine_path == null || aenux_path == null) {
                append_log ("[ERROR] Configuration path missing. Please run Installer.");
                return;
            }

            // Kron4ek Wine: binary is at wine_path/bin/wine
            string wine_bin = Path.build_filename (wine_path, "bin", "wine");
            string afterfx_exe = Path.build_filename (aenux_path, "AfterFX.exe");

            if (!FileUtils.test (wine_bin, FileTest.EXISTS)) {
                append_log ("[ERROR] wine binary not found at: " + wine_bin);
                return;
            }

            if (!FileUtils.test (afterfx_exe, FileTest.EXISTS)) {
                append_log ("[ERROR] AfterFX.exe not found at: " + afterfx_exe);
                return;
            }

            append_log ("[RUN] Launching After Effects with Wine " + wine_path + "...");
            string[] env = Utils.get_wine_env (wine_path, wineprefix);
            string[] cmd = {wine_bin, afterfx_exe};

            try {
                int stdout_fd;
                int stderr_fd;

                Process.spawn_async_with_pipes (
                    null,
                    cmd,
                    env,
                    SpawnFlags.SEARCH_PATH | SpawnFlags.DO_NOT_REAP_CHILD,
                    null,
                    out child_pid,
                    null,
                    out stdout_fd,
                    out stderr_fd
                );

                append_log ("[RUN] Process spawned (PID: %d)".printf ((int) child_pid));

                // Watch exit
                ChildWatch.add (child_pid, (pid, status) => {
                    append_log ("[RUN] After Effects exited with status %d".printf (status));
                    Process.close_pid (pid);
                    child_pid = 0;

                    // Clean Wine prefix processes
                    string? o, e;
                    Utils.kill_wine_processes (wine_path, wineprefix);
                    Utils.run_command ({"pkill", "-f", "AfterFX.exe"}, null, null, out o, out e);
                    Utils.run_command ({"pkill", "-f", "wine"}, null, null, out o, out e);
                    Utils.run_command ({"pkill", "-f", "wineserver"}, null, null, out o, out e);

                    Idle.add (() => {
                        this.close ();
                        return false;
                    });
                });

                // Live read stdout
                new Thread<int> ("stdout-reader", () => {
                    var dis = new DataInputStream (new UnixInputStream (stdout_fd, true));
                    string? line;
                    size_t len;
                    try {
                        while ((line = dis.read_line (out len, null)) != null) {
                            append_log ("[STDOUT] " + line);
                        }
                    } catch (Error err) {
                        append_log ("[RUN] Stdout reader closed: " + err.message);
                    }
                    return 0;
                });

                // Live read stderr
                new Thread<int> ("stderr-reader", () => {
                    var dis = new DataInputStream (new UnixInputStream (stderr_fd, true));
                    string? line;
                    size_t len;
                    try {
                        while ((line = dis.read_line (out len, null)) != null) {
                            append_log ("[STDERR] " + line);
                        }
                    } catch (Error err) {
                        append_log ("[RUN] Stderr reader closed: " + err.message);
                    }
                    return 0;
                });

            } catch (Error err) {
                append_log ("[ERROR] Launch failed: " + err.message);
                child_pid = 0;
            }
        }


        private void on_kill_clicked () {
            append_log ("[KILL] Terminating ALL Wine/After Effects processes...");
            string? wineprefix = Utils.get_config_value ("wineprefix");
            string? wine_path = Utils.get_config_value ("wine_path");

            // Direct SIGKILL on the spawned child process first
            if (child_pid != 0) {
                string? o2, e2;
                Utils.run_command ({"kill", "-9", child_pid.to_string ()}, null, null, out o2, out e2);
                child_pid = 0;
            }

            // Nuclear kill: wineserver + all wine sub-processes
            if (wine_path != null && wineprefix != null) {
                Utils.nuke_all_wine_processes (wine_path, wineprefix);
            } else {
                // Fallback if config not available
                string? o, e;
                Utils.run_command ({"pkill", "-9", "-f", "AfterFX.exe"}, null, null, out o, out e);
                Utils.run_command ({"pkill", "-9", "-f", "wineserver"}, null, null, out o, out e);
                Utils.run_command ({"pkill", "-9", "-f", "wine-preloader"}, null, null, out o, out e);
                Utils.run_command ({"pkill", "-9", "-f", "wine64-preloader"}, null, null, out o, out e);
                Utils.run_command ({"pkill", "-9", "-f", "wine"}, null, null, out o, out e);
            }

            append_log ("[KILL] All Wine processes terminated.");
            this.close ();
        }


        private void on_copy_logs_clicked () {
            var clipboard = Clipboard.get (Gdk.Atom.intern ("CLIPBOARD", false));
            clipboard.set_text (log_buffer.text, -1);
            
            var d = new MessageDialog (
                this, DialogFlags.MODAL, MessageType.INFO, ButtonsType.OK,
                "Logs copied to clipboard!"
            );
            d.run ();
            d.destroy ();
        }

        private bool on_delete_event (Gdk.EventAny event) {
            if (child_pid != 0) {
                var d = new MessageDialog (
                    this, DialogFlags.MODAL, MessageType.WARNING, ButtonsType.OK,
                    "After Effects is currently active. Please use 'Kill After Effects' or wait for the process to exit."
                );
                d.run ();
                d.destroy ();
                return true; // blocks window close
            }
            return false; // allows close
        }
    }
}
