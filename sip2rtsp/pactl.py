from subprocess import call

def create_pa_devices(sink="BaresipSpeaker", src="BaresipMicrophone"):
    load_sink = ["pactl", "load-module", "module-null-sink", f"sink_name={sink}", "format=s16le",
          "channels=1", "rate=8000", f"sink_properties=\"device.description=\'Baresip Speaker {sink}\'\""]
    print(" ".join(load_sink))
    err = call(load_sink)
    print(err)
    load_sink_input = ["pactl", "load-module", "module-remap-source", f"source_name={sink}Input", f"master={sink}.monitor",
          "format=s16le", "channels=1", "rate=8000", "channel_map=mono"]
    print(" ".join(load_sink_input))
    call(load_sink_input)
    print(err)
    load_src = ["pactl", "load-module", "module-null-sink", f"sink_name={src}", "format=s16le", "channels=1",
          "rate=8000", f"sink_properties=\"device.description='Baresip Microphone {src}'\""]
    print(" ".join(load_src))
    call(load_src)
    print(err)
    load_src_input = ["pactl", "load-module", "module-remap-source", f"source_name={src}Input", f"master={src}.monitor",
          "format=s16le", "channels=1", "rate=8000", "channel_map=mono"]
    print(" ".join(load_src_input))
    call(load_src_input)
    print(err)
#    raise Exception
