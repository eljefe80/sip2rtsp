from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Extra, Field, validator, parse_obj_as
from pydantic.fields import PrivateAttr

from sip2rtsp.const import (
    YAML_EXT,
)
from sip2rtsp.util import (
    load_config_with_no_duplicates,
)
from sip2rtsp.version import VERSION

logger = logging.getLogger(__name__)

SIP2RTSP_ENV_VARS = {k: v for k, v in os.environ.items() if k.startswith("SIP2RTSP_")}

class BaresipConfig():
    base_config = {
        "poll_method": "epoll",
        "sip_listen": "0.0.0.0:0",
        "sip_cafile": "/etc/ssl/certs/ca-certificates.crt",
        "sip_transports": "udp,tcp,tls,ws,wss",
        "sip_trans_def ": "udp",
        "sip_tos": "160",
        "call_local_timeout": "120",
        "call_max_calls": "1",
        "call_hold_other_calls": "yes",
        "audio_player": "pulse,BaresipSpeaker",
        "audio_source": "pulse,BaresipMicrophoneInput",
        "audio_alert": "alsa,default",
        "ausrc_srate": "8000",
        "auplay_srate": "8000",
        "audio_level": "no",
        "ausrc_format": "s16",
        "auplay_format": "s16",
        "auenc_format": "s16",
        "audec_format": "s16",
        "audio_buffer": "20-160",
        "audio_telev_pt": "101",
        "video_display": "v4l2loopback,/dev/video0",
        "v4l2loopback_width": "1280",
        "v4l2loopback_height": "720",
        "avcodec_passthrough": "/dev/video0",
        "rtp_tos": "184",
        "rtp_video_tos": "136",
        "rtp_ports": "10000-20000",
        "rtp_bandwidth": "6144",
        "rtcp_mux": "no",
        "jitter_buffer_type": "fixed",
        "jitter_buffer_delay": "5-10",
        "rtp_stats": "no",
        "module": [
          "g711.so",
          "pulse.so",
          "avcodec.so",
          "swscale.so",
          "v4l2loopback.so",
          "uuid.so",
          "stun.so",
          "turn.so",
          "ice.so",
          "ctrl_tcp",
        ],
        "module_app": [
           "account.so",
           "contact.so",
           "debug_cmd.so",
           "menu.so",
           "ctrl_tcp.so",
        ],
        "ctrl_tcp_listen": "0.0.0.0:4444",
        "opus_bitrate": "28000",
        "vumeter_stderr": "yes",
    }

    def __init__(self, name, config):
        self.config = self.base_config.copy()
        self.config["audio_player"] = config.sip.audio_device
        self.config["audio_source"] = config.sip.audio_source+"Input"
        self.config["video_display"] = f"v4l2loopback,{config.sip.video_device}"
        self.config["v4l2loopback_width"] = config.onvif.camera.width
        self.config["v4l2loopback_height"] = config.onvif.camera.height
        self.config["avcodec_passthrough"] = config.sip.video_device
        self.config["ctrl_tcp_listen"] = f"0.0.0.0:{config.sip.ctrl_port}"

    def write_config(self, config_file):
        ret  = Path(config_file).parents[0].mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w+') as f:
            for key, entry in self.config.items():
                print(type(entry))
                if isinstance(entry, list):
                    for ent in entry:
                        f.write(f"{key} {ent}\n")
                else:
                    f.write(f"{key} {entry}\n")
        with open(str(Path(config_file).parents[0]) + "/accounts", 'w+') as f:
            f.write("<sip:user1@office>;regint=0\n")

class Sip2RtspBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid

class LogLevelEnum(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class LoggerConfig(Sip2RtspBaseModel):
    default: LogLevelEnum = Field(
        default=LogLevelEnum.info, title="Default logging level."
    )
    logs: Dict[str, LogLevelEnum] = Field(
        default_factory=dict, title="Log level for specified processes."
    )


class RtspServerConfig(Sip2RtspBaseModel):
    launch_string: str = Field(
        default="", title="GStreamer RTSP server: launch string."
    )
    backchannel_launch_string: str = Field(
        default="", title="GStreamer RTSP server: backchannel launch string."
    )
    port: int = Field(
        default=8554, title="GStreamer RTSP server: TCP port to listen on."
    )
    mount_point: str = Field(default="", title="GStreamer RTSP server: mount point.")
    latency: int = Field(default=200, title="GStreamer RTSP server: latency.")
    enable_rtcp: bool = Field(
        default=False, title="GStreamer RTSP server: enable RTCP."
    )


class SipConfig(Sip2RtspBaseModel):
    remote_uri: str = Field(
        default="sip:11@10.10.10.80", title="SIP doorbell: remote URI to dial."
    )
    video_device: str = Field(
        default="/dev/video0", title="v4l2 device"
    )
    audio_device: str = Field(
        default="BaresipSpeakerInput", title="The shared audio sink between gstreamer and baresip"
    )
    audio_source: str = Field(
        default="BaresipMicrophone", title="The shared audio source between gstreamer and baresip"
    )
    ctrl_host: str = Field(
        default="0.0.0.0", title="Hostname of baresip service, usually localhost"
    )
    ctrl_port: int = Field(
        default=4444, title="Port of the baresip service, begin at 4444"
    )

class CameraConfig(Sip2RtspBaseModel):
    name: str = Field(
        default="sip2rtsp-cam", title="ONVIF server: Camera name to report"
    )
    location: str = Field(
        default="sip2rtsp-location", title="ONVIF server: Camera location to report"
    )
    eventTopicDoorbell: str = Field(
        default="tns1:Device/Trigger/DigitalInput", title="ONVIF server: Camera doorbell event topic"
    )
    snapshotUri: str = Field(default="http://10.10.10.10:54321/snapshot", title="ONVIF server: Camera snapshot URI to report")
    streamUri: str = Field(default="rtsp://10.10.10.70:8554/test", title="ONVIF server: Camera stream URI to report")
    width: int = Field(default=1920, title="ONVIF server: Camera width to report")
    height: int = Field(default=1080, title="ONVIF server: Camera height to report")
    fps: int = Field(default=30, title="ONVIF server: Camera fps to report")
    bitrate: int = Field(default=1000, title="ONVIF server: Camera bitrate to report")

class OnvifConfig(Sip2RtspBaseModel):
    listen_server_address: str = Field(
        default="0.0.0.0", title="ONVIF server: address to listen on."
    )
    listen_server_port: int = Field(default=10101, title="ONVIF server: port to listen on.")
    advertised_server_address: str = Field(
        default="10.10.10.70", title="ONVIF server: address to advertise."
    )
    advertised_server_port: int = Field(default=10101, title="ONVIF server: port to advertise.")
    hostname: str = Field(
        default="sip2rtsp-cam", title="ONVIF server: hostname to report"
    )
    camera: CameraConfig = Field(default_factory=CameraConfig, title="ONVIF camera configuration")

class ConnectionsConfig(Sip2RtspBaseModel):

    rtsp_server: RtspServerConfig = Field(
        default_factory=RtspServerConfig, title="GStreamer RTSP server configuration."
    )

    sip: SipConfig = Field(default_factory=SipConfig, title="SIP configuration.")

    onvif: OnvifConfig = Field(
        default_factory=OnvifConfig, title="ONVIF configuration."
    )

class Sip2RtspConfig(Sip2RtspBaseModel):
    environment_vars: Dict[str, str] = Field(
        default_factory=dict, title="sip2rtsp environment variables."
    )
    logger: LoggerConfig = Field(
        default_factory=LoggerConfig, title="Logging configuration."
    )
    connections: Dict[str, ConnectionsConfig] = Field(
        default_factory=dict, title="hash of connections"
    )

    @property
    def runtime_config(self) -> Sip2RtspConfig:
        """Merge config with globals."""
        config = self.copy(deep=True)
        print(config)
        return config

    @classmethod
    def parse_file(cls, config_file):
        with open(config_file) as f:
            raw_config = f.read()

        if config_file.endswith(YAML_EXT):
            config = load_config_with_no_duplicates(raw_config)
        elif config_file.endswith(".json"):
            config = json.loads(raw_config)

        return cls.parse_obj(config)

    @classmethod
    def parse_raw(cls, raw_config):
        config = load_config_with_no_duplicates(raw_config)
        return cls.parse_obj(config)
