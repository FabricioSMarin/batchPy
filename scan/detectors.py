import epics


def setup_scan_record(params):
    pass

def setup_hydra_controller(params):
    params["hydra_controller"].StartPosition.VAL = params["motors"]["x"].VAL + params["step_size"]
    params["hydra_controller"].EndPosition.VAL = params["motors"]["x"].VAL + params["width"]
    params["hydra_controller"].NumTriggers.VAL = params["loop1"].NPTS - 1
    return

def setup_xmap(params):
    epics.caput(params["xmap"].Capture.PROC, 1)
    return

def setup_tetramm(params):
    pass

def setup_xspress3(params):
    pass

def setup_struck(params):
    pass

def setup_eiger(params):
    pass

def setup_detectors(params):
    if "xmap" in params["detectors"]:
        setup_xmap(params)
    if "tetramm" in params["detectors"]:
        setup_tetramm(params)
    if "xspress3" in params["detectors"]:
        setup_xspress3(params)
    if "struck" in params["detectors"]:
        setup_struck(params)
    if "eiger" in params["detectors"]:
        setup_eiger(params)

def trigger_detectors(params):
    if params["scan_type"] == "fly":
        if "xspress3" in params["detectors"]:
            epics.caput(params["xspress3"].Capture.PROC, 1)
        if "xmap" in params["detectors"]:
            epics.caput(params["xmap"].Capture.PROC, 1)
        if "eiger" in params["detectors"]:
            epics.caput(params["eiger"].Capture.PROC, 1)
        if "tetramm" in params["detectors"]:
            epics.caput(params["tetramm"].Capture.PROC, 1)

    if "xspress3" in params["detectors"]:
        epics.caput(params["xspress3"].Capture.PROC, 1)
    if "xmap" in params["detectors"]:
        epics.caput(params["xmap"].Capture.PROC, 1)
    if "eiger" in params["detectors"]:
        epics.caput(params["eiger"].Capture.PROC, 1)
    if "tetramm" in params["detectors"]:
        epics.caput(params["tetramm"].Capture.PROC, 1)
    if "struck" in params["detectors"]:
        epics.caput(params["struck"].Acquire.PROC, 1)
