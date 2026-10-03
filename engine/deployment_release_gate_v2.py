
from pathlib import Path
import json
from datetime import datetime, timezone


class DeploymentReleaseGateV2:
    VERSION = "2.0"
    STATUS = "READY"
    DEPLOYMENT = "BLOCKED_UNTIL_FINAL_VERIFICATION"
    RELEASE = "BLOCKED_UNTIL_DEPLOYMENT"
    EXECUTION = "NOT_RUN"
    SAFE_STOP = True

    @classmethod
    def contract(cls):
        return {
            "gate": "DeploymentReleaseGateV2",
            "version": cls.VERSION,
            "status": cls.STATUS,
            "deployment": cls.DEPLOYMENT,
            "release": cls.RELEASE,
            "execution": cls.EXECUTION,
            "final_verification_required": True,
            "snapshot_required_before_release": True,
            "safe_stop": cls.SAFE_STOP,
        }

    @classmethod
    def evaluate(cls, final_verification=False, snapshot=False):
        deployment_allowed = bool(final_verification)
        release_allowed = bool(final_verification and snapshot)

        return {
            "deployment_allowed": deployment_allowed,
            "release_allowed": release_allowed,
            "deployment": "READY" if deployment_allowed else cls.DEPLOYMENT,
            "release": "READY" if release_allowed else cls.RELEASE,
            "execution": cls.EXECUTION,
            "safe_stop": cls.SAFE_STOP,
        }
