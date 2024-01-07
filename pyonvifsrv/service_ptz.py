import logging
import json
from pyonvifsrv.context import Context
from pyonvifsrv.service_base import ServiceBase
from pyonvifsrv.ciscoptz import CiscoPTZ

from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PtzService(ServiceBase):
    serviceName = "ptz"

    def __init__(self, context: Context):
        super().__init__(context)
        self.ptz = CiscoPTZ("10.200.1.142", ("admin", ""))

    def getNodes(self, data):
        logger.critical("pyonvifsrv: nodes")
        return '''
            <tptz:GetNodesResponse>
                <tptz:PTZNode token="default">
                    <tt:Name>default</tt:Name>
                    <tt:SupportedPTZSpaces>
                        <tt:AbsolutePanTiltPositionSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>0</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                            <tt:YRange>
                                <tt:Min>0</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:YRange>
                        </tt:AbsolutePanTiltPositionSpace>
                        <tt:AbsoluteZoomPositionSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>0</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                        </tt:AbsoluteZoomPositionSpace>
                        <tt:RelativePanTiltTranslationSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                            <tt:YRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:YRange>
                        </tt:RelativePanTiltTranslationSpace>
                        <tt:RelativePanTiltTranslationSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationSpaceFov</tt:URI>
                            <tt:XRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                            <tt:YRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:YRange>
                        </tt:RelativePanTiltTranslationSpace>
                        <tt:RelativeZoomTranslationSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/TranslationGenericSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                        </tt:RelativeZoomTranslationSpace>
                        <tt:ContinuousPanTiltVelocitySpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                            <tt:YRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:YRange>
                        </tt:ContinuousPanTiltVelocitySpace>
                        <tt:ContinuousZoomVelocitySpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/VelocityGenericSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>-1</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                        </tt:ContinuousZoomVelocitySpace>
                        <tt:PanTiltSpeedSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/GenericSpeedSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>0</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                        </tt:PanTiltSpeedSpace>
                        <tt:ZoomSpeedSpace>
                            <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/ZoomGenericSpeedSpace</tt:URI>
                            <tt:XRange>
                                <tt:Min>0</tt:Min>
                                <tt:Max>1</tt:Max>
                            </tt:XRange>
                        </tt:ZoomSpeedSpace>
                    </tt:SupportedPTZSpaces>
                    <tt:MaximumNumberOfPresets>16</tt:MaximumNumberOfPresets>
                    <tt:HomeSupported>false</tt:HomeSupported>
                    <tt:AuxiliaryCommands>AUX1</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX2</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX3</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX4</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX5</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX6</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX7</tt:AuxiliaryCommands>
                    <tt:AuxiliaryCommands>AUX8</tt:AuxiliaryCommands>
                </tptz:PTZNode>
            </tptz:GetNodesResponse>
        '''

    def getPresets(self, data):
        logger.critical(f"pyonvifsrv: presets: {data}")
        preset_xml = ""
        for i in (ptz.get_presets() or []):
            preset_xml += f"""
                <tptz:Preset token="{i}">
                    <tt:Name>{i}</tt:Name>
                </tptz:Preset>"""
        return f'''
            <tptz:GetPresetsResponse>{preset_xml}
            </tptz:GetPresetsResponse>
        '''

    def getNode(self, data):
        logger.critical(f"pyonvifsrv: node {data}")
        return '''
        '''

    def getStatus(self, data):
        logger.critical(f"pyonvifsrv: status {data} {self.ptz.get_x()}")
        status = '''
            <GetStatusResponse xmlns="http://www.onvif.org/ver20/ptz/wsdl">
                <tptz:PTZStatus>
                    <tt:Position>
                        <tt:PanTilt x="{x}" y="{x}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace" />
                        <tt:Zoom x="{zoom}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace" />
                    </tt:Position>
                    <tt:MoveStatus>
                        <tt:PanTilt>IDLE</tt:PanTilt>
                        <tt:Zoom>IDLE</tt:Zoom>
                    </tt:MoveStatus>
                    <tt:Error>OK</tt:Error>
                    <tt:UtcTime>{now}</tt:UtcTime>
                </tptz:PTZStatus>
            </GetStatusResponse>
        '''.format(
            now=datetime.now(timezone.utc).isoformat(),
            x=self.ptz.get_x(),
            y=self.ptz.get_y(),
            zoom=self.ptz.get_zoom()
        )
        logger.critical(f"pyonvifsrv:status {status}")
        return status

    def stop(self, data):
        logger.critical(f"pyonvifsrv: stop {json.dumps(data, indent=2)}")
        stop_arr = data.get('body').get('Stop')
        self.ptz.stop(pantilt=bool(stop_arr.get('PanTilt')), zoom=bool(stop_arr.get('Zoom')))
        return '''
        <tptz:StopResponse/>
        '''

    def relativeMove(self, data):
        logger.critical(f"pyonvifsrv: relativeMove {data}")
        return '''
        <tptz:RelativeZoomResponse/>
        '''

    def continuousMove(self, data):
        logger.critical(f"pyonvifsrv: continuousMove {json.dumps(data, indent=2)}")
        self.ptz.pantilt(data.get('body').get('ContinuousMove').get('Velocity').get('PanTilt'), style="Velocity")
        return '''
        <tptz:ContinuousMoveResponse/>
        '''

    def relativeZoom(self, data):
        logger.critical(f"pyonvifsrv: relativeZoom {data}")
        return '''
        <tptz:RelativeZoomResponse/>
        '''

    def continuousZoom(self, data):
        logger.critical(f"pyonvifsrv: continuousZoom {data}")
        self.ptz.zoom(data.get('body').get('ContinuousZoom').get('Velocity').get('Zoom'), style="Velocity")
        return '''
        <tptz:ContinuousZoomResponse/>
        '''

    def gotoPreset(self, data):
        logger.critical(f"pyonvifsrv: preset {data}")
        return '''
            <tptz:GotoPresetResponse></tptz:GotoPresetResponse>
        '''

    def gotoHomePosition(self, data):
        logger.critical(f"pyonvifsrv: home position {data}")
        return '''
             <tptz:GotoHomePositionResponse></tptz:GotoHomePositionResponse>
        '''

    def getConfigurations(self, data):
        logger.critical(f"pyonvifsrv: getconfig {data}")
        return '''
             <tptz:GetConfigurationsResponse>
                 <tptz:PTZConfiguration token="default">
                     <tt:Name>default</tt:Name>
                     <tt:UseCount>1</tt:UseCount>
                     <tt:NodeToken>default</tt:NodeToken>
                     <tt:DefaultAbsolutePantTiltPositionSpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:DefaultAbsolutePantTiltPositionSpace>
                     <tt:DefaultAbsoluteZoomPositionSpace>http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace</tt:DefaultAbsoluteZoomPositionSpace>
                     <tt:DefaultRelativePanTiltTranslationSpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:DefaultRelativePanTiltTranslationSpace>
                     <tt:DefaultRelativeZoomTranslationSpace>http://www.onvif.org/ver10/tptz/ZoomSpaces/TranslationGenericSpace</tt:DefaultRelativeZoomTranslationSpace>
                     <tt:DefaultContinuousPanTiltVelocitySpace>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:DefaultContinuousPanTiltVelocitySpace>
                     <tt:DefaultContinuousZoomVelocitySpace>http://www.onvif.org/ver10/tptz/ZoomSpaces/VelocityGenericSpace</tt:DefaultContinuousZoomVelocitySpace>
                     <tt:DefaultPTZSpeed>
                         <tt:PanTilt space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/GenericSpeedSpace" y="1" x="1"></tt:PanTilt>
                         <tt:Zoom space="http://www.onvif.org/ver10/tptz/ZoomSpaces/ZoomGenericSpeedSpace" x="1"></tt:Zoom>
                     </tt:DefaultPTZSpeed>
                     <tt:DefaultPTZTimeout>PT1093754.348S</tt:DefaultPTZTimeout>
                 </tptz:PTZConfiguration>
             </tptz:GetConfigurationsResponse>
        '''

    def getConfigurationOptions(self, data):
        logger.critical(f"pyonvifsrv: getconfigurationoptions {data}")
        return '''
             <tptz:GetConfigurationOptionsResponse>
                 <tptz:PTZConfigurationOptions>
                     <tt:Spaces>
                         <tt:AbsolutePanTiltPositionSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/PositionGenericSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>0</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                              <tt:YRange>
                                  <tt:Min>0</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:YRange>
                         </tt:AbsolutePanTiltPositionSpace>
                         <tt:AbsoluteZoomPositionSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/PositionGenericSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>0</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                         </tt:AbsoluteZoomPositionSpace>
                         <tt:RelativePanTiltTranslationSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationGenericSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                              <tt:YRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:YRange>
                          </tt:RelativePanTiltTranslationSpace>
                          <tt:RelativePanTiltTranslationSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/TranslationSpaceFov</tt:URI>
                              <tt:XRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                              <tt:YRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:YRange>
                         </tt:RelativePanTiltTranslationSpace>
                         <tt:RelativeZoomTranslationSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/TranslationGenericSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                         </tt:RelativeZoomTranslationSpace>
                         <tt:ContinuousPanTiltVelocitySpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                              <tt:YRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:YRange>
                         </tt:ContinuousPanTiltVelocitySpace>
                         <tt:ContinuousZoomVelocitySpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/VelocityGenericSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>-1</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                         </tt:ContinuousZoomVelocitySpace>
                         <tt:PanTiltSpeedSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/PanTiltSpaces/GenericSpeedSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>0</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                         </tt:PanTiltSpeedSpace>
                         <tt:ZoomSpeedSpace>
                              <tt:URI>http://www.onvif.org/ver10/tptz/ZoomSpaces/ZoomGenericSpeedSpace</tt:URI>
                              <tt:XRange>
                                  <tt:Min>0</tt:Min>
                                  <tt:Max>1</tt:Max>
                              </tt:XRange>
                         </tt:ZoomSpeedSpace>
                     </tt:Spaces>
                     <tt:PTZTimeout>
                         <tt:Min>PT0S</tt:Min>
                         <tt:Max>PT10S</tt:Max>
                     </tt:PTZTimeout>
                 </tptz:PTZConfigurationOptions>
             </tptz:GetConfigurationOptionsResponse>
        '''

    def getServiceCapabilities(self, data):
        logger.critical(f"pyonvifsrv: GetServiceCapabilities {data}")
        return '''
             <tds:GetServiceCapabilitiesResponse>
                 <tptz:Capabilities MoveStatus="true" StatusPosition="true"/>
             </tds:GetServiceCapabilitiesResponse>
        '''
