# -----------------------------------
# Set user-defined  input parameters
# -----------------------------------
workspace    = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\61_ASW00001-SF-F5P3BR\2012\VISIT_935\10_modelRuns\12June2015\Run1'
bfPoints     = 'bfPoints.shp'
bfPolyShp    = 'bfPolygon.shp'
inDet        = 'detDEM.img'
inDEM        = 'dem.img'
wePolyShp    = 'wePoly.shp'
bfXS         = 'bfXS.shp'

siteName     = 'Asotin'
intBFW       = 8.9        	# site integrated bankfull width (m)
intWW        = 4.8         	# site integrated wetted width (m)
fwSlope      = 0.9        	# Focal window size (m) for mean slope calc
memTh        = 0.5          # Membership threshold for crisp output
lowBFSlope	 = 8            # lower bankfull slope (in degress) threshold; used in planar
upBFSlope	 = 11           # upper bankfull slope (in degress) threshold; used in planar 
lowSlope     = 10           # lower slope (in degress) threshold; used in flooplain, terrace, hillslope
upSlope      = 15           # upper slope (in degress) threshold; used in flooplain, terrace, hillslope
lowCMSlope   = 15           # lower channel margin slope (in degress) threshold; used in bank + cutbank
upCMSlope    = 25           # upper channel margin slope (in degress) threshold; used in bank + cutbank
lowHADBF     = 1.0          # lower normalized height above detrended bankfull threshold
upHADBF      = 1.2          # upper normalized height above detrended bankfull threshold
lowRelief    = 0.8          # lower dem relief (m) threshold
upRelief     = 1.0          # upper dem relief (m) threshold
lowBFDist    = 0.1*intBFW   # lower bankfull distance threshold
upBFDist     = 0.2*intBFW   # upper bankfull distance threshold
fwRelief     = 0.5*intBFW   # Focal window size for dem relief call