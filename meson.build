project('io.github.cutefishaep.aenux', 'vala', 'c',
    version: '2.1.0',
    meson_version: '>= 0.56.0'
)

dependencies = [
    dependency('glib-2.0'),
    dependency('gobject-2.0'),
    dependency('gio-2.0'),
    dependency('gio-unix-2.0'),
    dependency('gtk+-3.0')
]

# Runner sources
runner_sources = files(
    'src/RunnerApp.vala',
    'src/RunnerWindow.vala',
    'src/Utils.vala'
)

executable(
    'aenux',
    sources: runner_sources,
    dependencies: dependencies,
    install: true
)

# Configurator/Installer sources
config_sources = files(
    'src/ConfigApp.vala',
    'src/InstallerWindow.vala',
    'src/ConfiguratorWindow.vala',
    'src/Utils.vala'
)

executable(
    'aenux_config',
    sources: config_sources,
    dependencies: dependencies,
    install: true
)
