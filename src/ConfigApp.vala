/*
 * ConfigApp.vala
 * Main Gtk.Application entry point for the AeNux Installer & Configurator.
 */

using GLib;
using Gtk;

namespace AeNux {
    public enum RuntimeMode {
        INSTALLER,
        CONFIGURATOR,
        CLEAN_REMOVE
    }

    public class ConfigApp : Gtk.Application {
        public static RuntimeMode active_mode = RuntimeMode.CONFIGURATOR;

        public ConfigApp () {
            Object (
                application_id: "io.github.cutefishaep.aenux.config",
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
            // Check if user_location is configured. If not, default to Installer.
            string? user_location = Utils.get_config_value ("user_location");
            if (user_location == null) {
                active_mode = RuntimeMode.INSTALLER;
            }

            if (active_mode == RuntimeMode.INSTALLER) {
                var win = new InstallerWindow (this);
                win.show_all ();
            } else if (active_mode == RuntimeMode.CONFIGURATOR) {
                var win = new ConfiguratorWindow (this);
                win.show_all ();
            }
        }

        public static int main (string[] args) {
            active_mode = RuntimeMode.CONFIGURATOR;
            for (int i = 1; i < args.length; i++) {
                if (args[i] == "--install") {
                    active_mode = RuntimeMode.INSTALLER;
                } else if (args[i] == "--remove") {
                    active_mode = RuntimeMode.CLEAN_REMOVE;
                }
            }

            if (active_mode == RuntimeMode.CLEAN_REMOVE) {
                return Utils.perform_clean_remove () ? 0 : 1;
            }

            var app = new ConfigApp ();
            string[] clean_args = { args[0] };
            return app.run (clean_args);
        }
    }
}
