# ---------------------------------------------------------------------------
# ELA detection threshold presets
#
# Each preset is a dictionary with:
#   variance_threshold  — std-dev cutoff for flagging a background patch
#   bright_threshold    — mean brightness ceiling for background classification
#   noisy_patch_ratio   — fraction of background patches that must be noisy
#                          to trigger an AI-generated verdict
#   patch_size          — side length of square analysis patches (pixels)
#
# To switch presets, change ELA_THRESHOLDS to reference a different dictionary.
# Preserve old presets for traceability; add new ones after each calibration.
# ---------------------------------------------------------------------------

thresholds_v1 = {
    "variance_threshold": 0.5,
    "bright_threshold": 10,
    "noisy_patch_ratio": 0.2147,
    "patch_size": 8,
}

thresholds_v2 = {
    "variance_threshold": 1.5,
    "bright_threshold": 30,
    "noisy_patch_ratio": 0.379,
    "patch_size": 8,
}

thresholds_v3 = {
    "variance_threshold": 1.2,
    "bright_threshold": 30,
    "noisy_patch_ratio": 0.4045,
    "patch_size": 16,
}

thresholds_v4 = {
    "variance_threshold": 1.2,
    "bright_threshold": 30,
    "noisy_patch_ratio": 0.4045,
    "patch_size": 16,
}

thresholds_v5 = {
    "variance_threshold": 1.5,
    "bright_threshold": 30,
    "noisy_patch_ratio": 0.379,
    "patch_size": 8,
}

# Active preset
ELA_THRESHOLDS = thresholds_v1
