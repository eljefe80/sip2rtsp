import asyncio
import logging
import os
import signal

from sip2rtsp.version import VERSION
from sip2rtsp.gi import GstRtspServer, GstRtsp
from sip2rtsp.baresip_ctrl import BaresipControl
from sip2rtsp.const import (
#    BARESIP_CTRL_HOST,
#    BARESIP_CTRL_PORT,
    BARESIP_CTRL_REQUEST_TIMEOUT,
    EVENT_TYPE,
)

logger = logging.getLogger(__name__)


class Sip2RtspApp:
    def __init__(self, aioloop, loop, config, environment_vars) -> None:
        self.ringCallback = None
        self.pendingIncomingCall = False

        self.aioloop = aioloop
        self.loop = loop
        self.config = config
        self.environment_vars = environment_vars

        self.server = GstRtspServer.RTSPOnvifServer.new()
        self.factory = GstRtspServer.RTSPOnvifMediaFactory.new()
        self.factory.set_media_gtype(GstRtspServer.RTSPOnvifMedia)

        self.factory.set_backchannel_launch(
            self.config.rtsp_server.backchannel_launch_string
        )
        self.factory.set_launch(self.config.rtsp_server.launch_string)

        self.factory.set_shared(False)
        self.factory.set_latency(self.config.rtsp_server.latency)
        self.factory.set_enable_rtcp(self.config.rtsp_server.enable_rtcp)
        # self.factory.set_backchannel_bandwidth(2000)
        # self.factory.set_protocols(GstRtsp.RTSPLowerTrans.TCP)
        # self.factory.set_profiles(GstRtsp.RTSPProfile.AVP)

        # Connect gstreamer signals
        self.server.connect("client-connected", self.client_connected)
        self.server.get_mount_points().add_factory(
            self.config.rtsp_server.mount_point, self.factory
        )
        self.server.set_service(str(self.config.rtsp_server.port))

        # Attach gstreamer RTSP server to our GLib event loop
        self.server.attach(self.loop.get_context())

        self.bs_ctrl = BaresipControl(
            config.sip.ctrl_host,
            config.sip.ctrl_port,
            BARESIP_CTRL_REQUEST_TIMEOUT
        )
        self.bs_ctrl.set_callback(self.event_handler)


    def set_RingingCallback(self, callback):
        """Set the callback function to be called when an incoming call event is signalled"""
        self.ringCallback = callback

    def set_environment_vars(self) -> None:
        for key, value in self.environment_vars.items():
            os.environ[key] = value

    async def start(self) -> None:
        logger.info(f"Starting SIP2RTSP ({VERSION})")
        logger.info(f"GST RTSP server is listening on {self.server.get_address()}:{self.server.get_service()}")
        try:
            self.set_environment_vars()
        except Exception as e:
            print(e)
            os.kill(os.getpid(), signal.SIGTERM)

        await self.bs_ctrl.start()
        async def dial():
            if self.pendingIncomingCall:
                logger.info("ONVIF backchannel requested. Answering incoming call...")
                await self.bs_ctrl.accept()
                logger.info("Answering done...")
            else:
                logger.info("ONVIF backchannel requested. Dialing...")
                await self.bs_ctrl.dial(self.config.sip.remote_uri)
                logger.info("Dialing done...")

        asyncio.run_coroutine_threadsafe(dial(), self.aioloop)

    async def stop(self) -> None:
        # Try to hang up any active calls gracefully
        callstat = await self.bs_ctrl.callstat()
        if callstat:
            if "(no active calls)" not in callstat:
                logger.info(f"stop: Hanging up...")
                await self.bs_ctrl.hangup()
                logger.info(f"stop: Hanging up done...")
        else:
            # If callstat() fails, we assume there is an active call
            # This might fail too...
            await self.bs_ctrl.hangup()
        logger.info(f"Stopped SIP2RTSP ({VERSION})")

    def event_handler(self, data):
        # logger.debug("Event: " + str(data))
        if data["type"] == EVENT_TYPE.CALL_INCOMING:
            logger.info("Incoming call from {peeruri}".format(peeruri=data["peeruri"]))
            self.pendingIncomingCall = True
            if self.ringCallback:
                self.ringCallback(data["peeruri"])
        elif data["type"] == EVENT_TYPE.CALL_CLOSED:
            logger.info("Call closed from {peeruri}".format(peeruri=data["peeruri"]))
            self.pendingIncomingCall = False
        elif data["type"] == EVENT_TYPE.CALL_ESTABLISHED:
            logger.info(
                "Call established from {peeruri}".format(peeruri=data["peeruri"])
            )

    def client_play_request(self, client, context: GstRtspServer.RTSPContext):
        logger.debug(
            "Received PLAY request from {remoteip}".format(
                remoteip=client.get_connection().get_ip()
            )
        )
        reqmsg: GstRtsp.RTSPMessage = context.request
        # reqmsg.dump()
        res, value = reqmsg.get_header(GstRtsp.RTSPHeaderField.REQUIRE, 0)
        if res == GstRtsp.RTSPResult.OK:
            logger.debug("PLAY request header: Require: {value}".format(value=value))

    def client_setup_request(self, client, context: GstRtspServer.RTSPContext):
        control = context.stream.get_control()
        caps = context.stream.get_caps()
        caps = caps.to_string() if caps else "n/a"
        logger.info(
            "Received SETUP request from {remoteip}: control: {control}, caps: {caps}".format(
                remoteip=client.get_connection().get_ip(), control=control, caps=caps
            )
        )
        uri: GstRtsp.RTSPUrl = context.uri
#        uri.dump()
#        print(dir(uri))
        # res, value = reqmsg.get_header(GstRtsp.RTSPHeaderField.URI, 0)
#        logger.info(f"Received SETUP request res: {res}, value: {value}")
        #if res == GstRtsp.RTSPResult.OK:
#            logger.debug("SETUP request header: Require: {value}".format(value=value))
        async def dial():
            callstat = await self.bs_ctrl.callstat()
            if callstat:
                if "(no active calls)" in callstat:
                    if self.pendingIncomingCall:
                        logger.info("ONVIF backchannel requested. Answering incoming call...")
                        await self.bs_ctrl.accept()
                        logger.info("Answering done...")
                    else:
                        logger.info("ONVIF backchannel requested. Dialing...")
                        await self.bs_ctrl.dial(self.config.sip.remote_uri)
                        logger.info("Dialing done...")

        asyncio.run_coroutine_threadsafe(dial(), self.aioloop)


        if "stream=2" in uri.abspath:
            logger.debug("TODO: add muting")

    def client_describe_request(self, client, context: GstRtspServer.RTSPContext):
        logger.debug(
            "Received DESCRIBE request from: {remoteip}".format(
                remoteip=client.get_connection().get_ip()
            )
        )
        reqmsg: GstRtsp.RTSPMessage = context.request
        # reqmsg.dump()
        res, value = reqmsg.get_header(GstRtsp.RTSPHeaderField.REQUIRE, 0)
        if res == GstRtsp.RTSPResult.OK:
            logger.debug(
                "DESCRIBE request header: Require: {value}".format(value=value)
            )

    def client_teardown_request(self, client, context: GstRtspServer.RTSPContext):
        logger.debug(
            "Received TEARDOWN request from {remoteip}".format(
                remoteip=client.get_connection().get_ip()
            )
        )
        uri: GstRtsp.RTSPUrl = context.uri
        if "stream=2" in uri.abspath:
                async def hangup():
                    logger.info("ONVIF backchannel TEARDOWN request. Hanging up...")
                    await self.bs_ctrl.hangup()
                    logger.info("Hanging up done...")
                    self.pendingIncomingCall = False

                asyncio.run_coroutine_threadsafe(hangup(), self.aioloop)

    def client_closed(self, client):
        logger.debug(
            "RTSP client connection from {remoteip} closed".format(
                remoteip=client.get_connection().get_ip()
            )
        )

        async def hangup():
            logger.info("RTSP client connection connection was closed.")
            # Try to hang up any active calls gracefully
            callstat = await self.bs_ctrl.callstat()
            if callstat:
                if "(no active calls)" not in callstat:
                    logger.info(f"client_closed: Hanging up...")
                    await self.bs_ctrl.hangup()
                    logger.info(f"client_closed: Hanging up done...")
            else:
                # If callstat() fails, we assume there is an active call
                # This might fail too...
                await self.bs_ctrl.hangup()

            self.pendingIncomingCall = False

        asyncio.run_coroutine_threadsafe(hangup(), self.aioloop)

    # def client_send_message(self, client, _whatsthis, message):
    #     logger.debug(
    #         "Sending message to {remoteip} body: \n{body}".format(
    #             remoteip=client.get_connection().get_ip(),
    #             body=message.get_body().data.decode("utf-8"),
    #         )
    #     )

    def client_connected(self, server, client):
        logger.info(
            "RTSP client connected from {remoteip}".format(
                remoteip=client.get_connection().get_ip()
            )
        )
        client.connect("play-request", self.client_play_request)
        client.connect("setup-request", self.client_setup_request)
        client.connect("describe-request", self.client_describe_request)
        client.connect("teardown-request", self.client_teardown_request)
        # client.connect("closed", self.client_closed)
        # client.connect("send_message", self.client_send_message)
