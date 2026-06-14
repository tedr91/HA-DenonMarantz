DOMAIN = "denon_marantz"
DEFAULT_NAME = "Denon Marantz AVR"
DEFAULT_PORT = 23

CONF_PORT = "port"
CONF_ADD_EXTENDED_ENTITIES = "add_extended_entities"
CONF_INPUT_FILTER = "input_filter"
DEFAULT_ADD_EXTENDED_ENTITIES = False
DEFAULT_INPUT_FILTER = ""

SERVICE_SEND_COMMAND = "send_command"
ATTR_COMMAND = "command"
ATTR_ENTRY_ID = "entry_id"
ATTR_TIMEOUT = "timeout"
ATTR_EXPECTED_PREFIXES = "expected_prefixes"
ATTR_ALLOW_TIMEOUT = "allow_timeout"

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

DIALOGUE_ENHANCER_QUERY_COMMAND = "PSDIL ?"
DIALOGUE_ENHANCER_RESPONSE_PREFIX = "PSDIL"
DIALOGUE_ENHANCER_OPTIONS: list[str] = ["Off", "Low", "Medium", "High"]

DYNAMIC_COMPRESSION_QUERY_COMMAND = "PSDRC ?"
DYNAMIC_COMPRESSION_RESPONSE_PREFIX = "PSDRC"
DYNAMIC_COMPRESSION_OPTIONS: list[str] = ["Off", "Auto", "Low", "Medium", "High"]

LOUDNESS_QUERY_COMMAND = "PSLOM ?"
LOUDNESS_RESPONSE_PREFIX = "PSLOM"
LOUDNESS_OPTIONS: list[str] = ["Off", "On"]

ACTIVE_SPEAKERS_QUERY_COMMAND = "CV?"
ACTIVE_SPEAKERS_RESPONSE_PREFIX = "CV"
ACTIVE_SPEAKERS_TERMINATOR = "CVEND"

# Maps Channel Volume (CV) speaker codes to human-friendly names. The receiver
# only reports the channels that are active for the current surround mode, so the
# set of codes returned by "CV?" represents the currently active speakers. The
# insertion order below is the canonical display order for the sensor state.
CHANNEL_MAP: dict[str, str] = {
	"FL": "Front Left",
	"FR": "Front Right",
	"C": "Center",
	"SW": "Subwoofer",
	"SW2": "Subwoofer 2",
	"SW3": "Subwoofer 3",
	"SW4": "Subwoofer 4",
	"SL": "Surround Left",
	"SR": "Surround Right",
	"SBL": "Surround Back Left",
	"SBR": "Surround Back Right",
	"SB": "Surround Back",
	"FHL": "Front Height Left",
	"FHR": "Front Height Right",
	"FWL": "Front Wide Left",
	"FWR": "Front Wide Right",
	"TFL": "Top Front Left",
	"TFR": "Top Front Right",
	"TML": "Top Middle Left",
	"TMR": "Top Middle Right",
	"TRL": "Top Rear Left",
	"TRR": "Top Rear Right",
	"RHL": "Rear Height Left",
	"RHR": "Rear Height Right",
	"FDL": "Front Dolby Left",
	"FDR": "Front Dolby Right",
	"SDL": "Surround Dolby Left",
	"SDR": "Surround Dolby Right",
	"BDL": "Back Dolby Left",
	"BDR": "Back Dolby Right",
	"SHL": "Surround Height Left",
	"SHR": "Surround Height Right",
	"TS": "Top Surround",
	"CH": "Center Height",
}

# Channel codes that represent LFE / subwoofer outputs. These contribute to the
# ".Y" (middle) figure of an "X.Y.Z" speaker-layout string.
SUBWOOFER_CHANNELS: frozenset[str] = frozenset({"SW", "SW2", "SW3", "SW4"})

# Channel codes that represent overhead / height effect speakers. These contribute
# to the trailing ".Z" figure of an "X.Y.Z" speaker-layout string. Every channel
# that is neither a subwoofer nor a height speaker is treated as an ear-level
# "bed" channel and contributes to the leading "X" figure.
HEIGHT_CHANNELS: frozenset[str] = frozenset(
	{
		"FHL",
		"FHR",
		"TFL",
		"TFR",
		"TML",
		"TMR",
		"TRL",
		"TRR",
		"RHL",
		"RHR",
		"FDL",
		"FDR",
		"SDL",
		"SDR",
		"BDL",
		"BDR",
		"SHL",
		"SHR",
		"TS",
		"CH",
	}
)
