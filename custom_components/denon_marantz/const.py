DOMAIN = "denon_marantz"
DEFAULT_NAME = "Denon Marantz AVR"
DEFAULT_PORT = 23

CONF_PORT = "port"

DEFAULT_SOUND_MODES: list[str] = [
	"STEREO",
	"DIRECT",
	"PURE DIRECT",
	"DOLBY DIGITAL",
	"DTS SURROUND",
	"MUSIC",
	"MOVIE",
	"GAME",
	"AURO3D",
]

DEFAULT_INPUT_SOURCES: list[str] = [
	"CD",
	"TV",
	"SAT/CBL",
	"GAME",
	"AUX",
	"BLUETOOTH",
	"TUNER",
]

STATUS_SENSOR_COMMANDS: tuple[tuple[str, str, str], ...] = (
	("cinema_eq_status", "PSCINEMA EQ ?", "PSCINEMA EQ"),
	("dynamic_eq_status", "PSDYNEQ ?", "PSDYNEQ"),
	("dynamic_volume_status", "PSDYNVOL ?", "PSDYNVOL"),
	("multi_eq_status", "PSMULTEQ ?", "PSMULTEQ"),
)
