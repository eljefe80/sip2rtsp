import xml.etree.ElementTree as et
import time
import requests
import atexit
import uuid
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

MAX_X = 17000
MAX_Y = 9000
MAX_X_VEL = 24
MAX_Y_VEL = 24
UP = 1
DOWN = -1
RIGHT = -1
LEFT = 1
POS_X = 10000
POS_Y = 2500
POS_Z = 11800


def get_session_id(cookies):
    for cookie in cookies.split(";"):
        vals = cookie.split("=")
        if vals[0] == "SecureSessionId":
            return vals[1]
    return None

def dir_or_stop(val, pos, neg):
    if val is not None:
        return "Stop" if val == 0 else (
            pos if val > 0 else neg
         )
    return None

def is_float(string):
    print(f"Got here is_float {string}")
    try:
        float(string)
        return True
    except ValueError:
        return False

def position_normalize(ptz, val):
    match ptz:
       case "Pan":
            return (1/POS_X) * val
       case "Tilt":
            return (1/POS_Y) * val
       case "Zoom":
            return (1/POS_Z) * val

class CiscoPTZ:

    def __init__(self, addr, auth):
        self.auth = auth
        self.addr = addr
        resp = requests.post(
             'http://10.200.1.142/xmlapi/session/begin',
             data={},
             auth=('admin', ''),
             verify=False
        )
        self.session_id = get_session_id(
             resp.headers['Set-Cookie']
        )
        self.headers = {
            "Content-Type": "text/xml",
        }
        self.cookies = {
            "SecureSessionId": self.session_id
        }
#        self.position_reset()
        atexit.register(self.__close__)

    def __close__(self):
        req = requests.post(
            f"http://{self.addr}/xmlapi/session/end",
            headers=self.headers,
            cookies=self.cookies,
            data={},
            verify=False
        )
        return req

    def __post__(self, data={}):
        req = requests.post(
            f"http://{self.addr}/putxml",
            headers=self.headers,
            cookies=self.cookies,
            data=data,
            verify=False
        )
        xml = et.fromstring(req.content)
        return xml

    def __get__(self, path, data={}):
        req = requests.get(
            f"http://{self.addr}/getxml?location={path}",
            headers=self.headers,
            cookies=self.cookies,
            data=data,
            verify=False
        )
        xml = et.fromstring(req.content)
        return xml

    def get_configuration(self):
        return self.__post__("configuration.xml")

    def get_capabilities(self):
        return self.__get__("/Status/Cameras/Camera") #/1/Capabilities/Options")

    def preset_activate(self, preset=1):
        if isinstance(preset, int) or preset.isdigit():
            body = f"""
                <Command>
                    <Camera>
                        <Preset>
                            <Activate command="True">
                                 <PresetId>{preset}</PresetId>
                            </Activate>
                        </Preset>
                    </Camera>
                </Command>
            """
            return self.__post__(body)
        return None
    def get_presets(self, camera_id=1):
        presets = []
        for preset in (self.preset_list(camera_id).iter() or []):
            if "Preset" in preset.tag:
                presets.append(preset.text)
        return presets

    def preset_list(self, camera_id=1):
        if isinstance(camera_id, int) or camera_id.isdigit():
            body = f"""
                <Command>
                    <Camera>
                        <Preset>
                            <List command="True">
                                 <CameraId>{camera_id}</CameraId>
                            </List>
                        </Preset>
                    </Camera>
                </Command>
            """
            return self.__post__(body)
        return None

    def preset_store(self, camera_id=1, name=None, preset_id=None, default_position=False):
        if (isinstance(camera_id, int) or camera_id.isdigit()):
            preset_id_s = "" if preset_id is None else f"""
                                 <PresetId>{preset_id}</PresetId>"""
            default_position_s = "True" if default_position else "False"
            name_s = name if name is not None else f"Preset-{uuid4()[-4:]}"
            body = f"""
                <Command>
                    <Camera>
                        <Preset>
                             <Store command="True">
                                 <CameraId>{camera_id}</CameraId>{preset_id_s}
                                 <Name>{name_s}</Name>
                                 <DefaultPosition>{default_position_s}</DefaultPosition>
                            </Store>
                        </Preset>
                    </Camera>
                </Command>
            """
            print(body)
            return self.__post__(body)
        return None

    def position_reset(self, camera_id=1, axis="all"):
        if (isinstance(camera_id, int) or camera_id.isdigit()) and\
               axis.lower() in ["all", "focus", "pantilt", "zoom"]:
            body = f"""
                <Command>
                    <Camera>
                        <PositionReset command="True">
                             <CameraId>{camera_id}</CameraId>
                             <Axis>{axis}</Axis>
                        </PositionReset>
                    </Camera>
                </Command>
            """
            return self.__post__(body)
        return None

    def position_set(self, camera_id=1, pan=None, tilt=None, zoom=None):
        if ((isinstance(camera_id, int) or camera_id.isdigit()) and\
               [x for x in (pan, tilt, zoom) if x is not None]):
            panb = "" if pan is None else f"""
                             <Pan>{int(pan)}</Pan>"""
            tiltb = "" if tilt else f"""
                             <Tilt>{int(tilt)}</Tilt>"""
            zoomb = "" if zoom else f"""
                             <Zoom>{int(zoom)}</Zoom>"""
            body = f"""
                <Command>
                    <Camera>
                        <PositionSet command="True">
                             <CameraId>{camera_id}</CameraId>{panb}{tiltb}{zoomb}
                        </PositionSet>
                    </Camera>
                </Command>
            """
            return self.__post__(body)
        return None

    def ramp(self, camera_id=1, pan=None, tilt=None, zoom=None):
        if (isinstance(camera_id, int) or camera_id.isdigit()):
            print("ramp: Got here")

            pandir = "" if pan is None else f"""
                             <Pan>{dir_or_stop(pan, "Right", "Left")}</Pan>"""
            panb = "" if pan in [None, 0] else f"""
                             <PanSpeed>{abs(int(pan))}</PanSpeed>"""
            tiltdir = "" if tilt is None  else f"""
                             <Tilt>{dir_or_stop(tilt, "Up", "Down")}</Tilt>"""
            tiltb = "" if tilt in [None, 0]  else f"""
                             <TiltSpeed>{abs(int(tilt))}</TiltSpeed>"""
            zoomdir = "" if zoom in [None, 0] else f"""
                             <Zoom>{dir_or_stop(zoom, "Out", "In")}</Zoom>"""
            zoomb = "" if zoom in [None, 0] else f"""
                             <ZoomSpeed>{abs(int(zoom))}</ZoomSpeed>"""
            body = f"""
                <Command>
                    <Camera>
                        <Ramp command="True">
                             <CameraId>{camera_id}</CameraId>{panb}{pandir}{tiltb}{tiltdir}{zoomb}{zoomdir}
                        </Ramp>
                    </Camera>
                </Command>
            """
            print(body)
            req = self.__post__(body)
            print(et.dump(req))
            return req
        print("ramp: got here 2")
        return None

    def status_position(self, camera_id=1, axis=None):
        if axis not in ["Pan", "Tilt", "Zoom"]:
            return None
        req = self.__get__(f"/Status/Cameras/Camera/{(str(camera_id)+'/') if camera_id != 1 else ''}Position/{axis}")
        print(et.dump(req))
        for elem in req.iter():
            if elem.tag == axis:
                return position_normalize(axis, float(elem.text))
        return 0

    def pan_right(self, move):
        return self.pan(-move)

    def pan_left(self, move):
        """input: absolute distance to move"""
        return self.pan(move)

    def pan(self, move, continuous=False):
        """ input: move value 0-1 """
        if continuous:
            return self.pan_continuous(move)
        return self.pan_absolute(move)

    def pan_absolute(self, move):
        """ input: move value 0-1 """
        if not (isinstance(move, float) or move.isdigit()):
            return None
        abs_move = float(move) * MAX_X
        return self.position_set(pan=abs_move)

    def pan_continuous(self, move):
        """ input: move value 0-1 """
        if not (isinstance(move, float) or move.isdigit()):
            return None
        abs_vel = float(move) * MAX_X_VEL
        return self.ramp(pan=abs_vel)

    def tilt_up(self, move):
        return self.tilt(move)

    def tilt_down(self, move):
        return self.tilt(-move)

    def tilt(self, move, continuous=False):
        """ input: move value 0-1 """
        if continuous:
            return self.tilt_continuous(move)
        return self.tilt_absolute(move)

    def tilt_absolute(self, move):
        if not (isinstance(move, float) or is_float(move)):
            return None
        abs_move = float(move) * MAX_Y
        return self.position_set(tilt=abs_move)

    def tilt_continuous(self, move):
        if not (isinstance(move, float) or move.isdigit()):
            return None
        abs_vel = float(move) * MAX_Y_VEL
        return self.ramp(tilt=abs_vel)

    def pantilt_absolute(self, pan, tilt):
        if not ((isinstance(pan, float) or pan.isdigit()) and
               (isinstance(tilt, float) or tilt.isdigit())):
            return None
        abs_tilt_move = float(tilt) * MAX_Y
        abs_pan_move = float(pan) * MAX_X

        return self.position_set(pan=abs_pan_move, tilt=abs_tilt_move)

    def pantilt_continuous(self, pan, tilt):
        print(f"Got here {pan}, {tilt}")
        if not ((isinstance(pan, float) or is_float(pan)) and
               (isinstance(tilt, float) or is_float(tilt))):
            print("Got here: pantilt_continuous 1")
            return None
        print("Got here: pantilt_continuous 2")
        abs_tilt_move = float(f"{tilt}".strip()) * MAX_Y_VEL
        print(f"Got here: pantilt_continuous 3 {abs_tilt_move}")
        abs_pan_move = float(f"{pan}".strip()) * MAX_X_VEL
        print(f"Got here: pantilt_continuous 4 {abs_pan_move}")

        return self.ramp(pan=abs_pan_move, tilt=abs_tilt_move)

    def pantilt(self, pantilthash=None, style=None):
        pos_x = pantilthash.get('@x')
        pos_y = pantilthash.get('@y')
        if style == "Velocity":
            print("pantilt: got here")
            return self.pantilt_continuous(pan=pos_x, tilt=pos_y)
        return self.pantilt_absolute(pan=pos_x, tilt=pos_y)

    def zoom(self, zoom=None, style=None):
        if style == "Velocity":
            print("pantilt: got here")
            return self.pantilt_continuous(zoom=zoom)
        return self.pantilt_absolute(zoom=zoom)

    def stop(self, pantilt=False, zoom=False):
        print(f"stop: Got here {pantilt} {zoom}")
        if pantilt:
            print("stop: Got here pantilt")
            self.ramp(pan=0, tilt=0)
        if zoom:
            print("stop: Got here zoom")
            self.ramp(zoom=0)

    def get_x(self):
        return self.status_position(axis='Pan')

    def get_y(self):
        return self.status_position(axis='Tilt')

    def get_zoom(self):
        return self.status_position(axis='Zoom')

if __name__ == '__main__':
    ptz = CiscoPTZ("10.200.1.142", ("admin", ""))

#    print(ptz.getConfiguration().text)
#    print(ptz.getConfiguration().headers)
#    print(et.dump(ptz.getCapabilities()))
#    print(et.dump(ptz.presetList(1)))
#    print(et.dump(ptz.presetActivate(1)))
#    print(et.dump(ptz.positionReset()))
#    time.sleep(20)
#    ret = ptz.tilt(.5, continuous=True)
#    print(ret)
#    print(et.dump(ret))
#    ret = ptz.tilt(0)
#    print(ret)
#    print(et.dump(ret))
    ret = ptz.get_x()
    print(ret)
#    print(et.dump(ret))
    ret = ptz.get_y()
#    print(et.dump(ret))
    if ret:
        print(ret)
    else:
        print("Problem")
    for i in range(1, 70):
       ptz.pan(24/MAX_X_VEL, continuous=True)
       ptz.stop(pantilt=True)
#    ret = ptz.preset_store(name="Home", preset_id=1, default_position=True)
    if ret:
        print(ret)
    del ptz
