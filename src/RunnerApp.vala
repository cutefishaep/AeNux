/*
 * RunnerApp.vala
 * Main Gtk.Application entry point for the AeNux Runner.
 */

using GLib;
using Gtk;

namespace AeNux {
    public class RunnerApp : Gtk.Application {
        public RunnerApp () {
            Object (
                application_id: "io.github.cutefishaep.aenux",
                flags: ApplicationFlags.DEFAULT_FLAGS
            );
        }

        protected override void startup () {
            base.startup ();

            var css_provider = new CssProvider ();
            try {
                string exe_dir = Utils.get_executable_dir ();
                string css_path = Path.build_filename (exe_dir, "src", "style.css");
                if (!FileUtils.test (css_path, FileTest.EXISTS)) {
                    css_path = Path.build_filename (exe_dir, "style.css");
                }
                css_provider.load_from_path (css_path);
                StyleContext.add_provider_for_screen (
                    Gdk.Screen.get_default (),
                    css_provider,
                    STYLE_PROVIDER_PRIORITY_APPLICATION
                );
            } catch (Error e) {
                stderr.printf ("Failed to load CSS: %s\n", e.message);
            }

            // Sync with system theme preference
            if (SettingsSchemaSource.get_default ().lookup ("org.gnome.desktop.interface", true) != null) {
                var settings = new GLib.Settings ("org.gnome.desktop.interface");
                var gtk_settings = Gtk.Settings.get_default ();
                
                settings.changed["color-scheme"].connect (() => {
                    string scheme = settings.get_string ("color-scheme");
                    string theme = settings.get_string ("gtk-theme");
                    gtk_settings.gtk_application_prefer_dark_theme = (scheme == "prefer-dark" || theme.down ().contains ("dark"));
                });
                
                settings.changed["gtk-theme"].connect (() => {
                    string scheme = settings.get_string ("color-scheme");
                    string theme = settings.get_string ("gtk-theme");
                    gtk_settings.gtk_application_prefer_dark_theme = (scheme == "prefer-dark" || theme.down ().contains ("dark"));
                });

                string scheme = settings.get_string ("color-scheme");
                string theme = settings.get_string ("gtk-theme");
                gtk_settings.gtk_application_prefer_dark_theme = (scheme == "prefer-dark" || theme.down ().contains ("dark"));
            }
        }

        protected override void activate () {
            string? show_ui = Utils.get_config_value ("show_runner_ui");
            if (show_ui == "false") {
                hold ();
                new Thread<int> ("headless-runner", () => {
                    Utils.run_headless_runner ();
                    release ();
                    return 0;
                });
            } else {
                var win = new RunnerWindow (this);
                win.show_all ();
            }
        }

        public static int main (string[] args) {
            var app = new RunnerApp ();
            string[] clean_args = { args[0] };
            return app.run (clean_args);
        }
    }
}
