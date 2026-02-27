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
	("multi_eq_status", "PSMULTEQ ?", "PSMULTEQ"),
)

DYNAMIC_EQ_QUERY_COMMAND = "PSDYNEQ ?"
DYNAMIC_EQ_RESPONSE_PREFIX = "PSDYNEQ"

DYNAMIC_VOLUME_QUERY_COMMAND = "PSDYNVOL ?"
DYNAMIC_VOLUME_RESPONSE_PREFIX = "PSDYNVOL"
DYNAMIC_VOLUME_OPTIONS: list[str] = ["Off", "Light", "Medium", "Heavy"]
