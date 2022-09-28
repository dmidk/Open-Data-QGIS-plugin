depth_para_dkss = ['salinity_', 'water_temp_','v_comp_cur_','u_comp_cur_']

################ nsbs #########################

band_depth_nsbs = [4,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,
                   61,63,65,67,69,71,73,75,77,79,82,88,96,113,138,175,225,275,325,375,425,475,525]
# Salinity
band_num_salinity_nsbs = list(range(160,210))
salinity_nsbs = dict(zip(band_depth_nsbs,band_num_salinity_nsbs))
# Water temperature
band_num_water_temp_nsbs = list(range(110,160))
water_temp_nsbs = dict(zip(band_depth_nsbs,band_num_water_temp_nsbs))
# v-component of current
band_num_v_current_nsbs = list(range(60,110))
v_current_nsbs = dict(zip(band_depth_nsbs,band_num_v_current_nsbs))
# u-component of current
band_num_u_current_nsbs = list(range(10,60))
u_current_nsbs = dict(zip(band_depth_nsbs,band_num_u_current_nsbs))

################# idw #######################
band_depth_idw = [1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,
                  29,30,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61,63,65,67,69,71,73,75]
# Salinity
band_num_salinity_idw = list(range(166,218))
salinity_idw = dict(zip(band_depth_idw,band_num_salinity_idw))
# Water temperature
band_num_water_temp_idw = list(range(114,166))
water_temp_idw = dict(zip(band_depth_idw,band_num_water_temp_idw))
# v-component of current
band_num_v_current_idw = list(range(62,114))
v_current_idw = dict(zip(band_depth_idw,band_num_v_current_idw))
# v-component of current
band_num_u_current_idw = list(range(10,62))
u_current_idw = dict(zip(band_depth_idw,band_num_u_current_idw))

################## ws ##########################
band_depth_ws = [4,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49]
# Salinity
band_num_salinity_ws = list(range(76,98))
salinity_ws = dict(zip(band_depth_ws,band_num_salinity_ws))
# Water temperature
band_num_water_temp_ws = list(range(54,76))
water_temp_ws = dict(zip(band_depth_ws,band_num_water_temp_ws))
# v-component of current
band_num_v_current_ws = list(range(32,54))
v_current_ws = dict(zip(band_depth_ws,band_num_v_current_ws))
# v-component of current
band_num_u_current_ws = list(range(10,32))
u_current_ws = dict(zip(band_depth_ws,band_num_u_current_ws))

######################## if #######################
band_depth_if = [1,3,4,5,6,7,8,9,10,11]
# Salinity
band_num_salinity_if = list(range(40,50))
salinity_if = dict(zip(band_depth_if,band_num_salinity_if))
# Water temperature
band_num_water_temp_if = list(range(30,40))
water_temp_if = dict(zip(band_depth_if,band_num_water_temp_if))
# v-component of current
band_num_v_current_if = list(range(20,30))
v_current_if = dict(zip(band_depth_if,band_num_v_current_if))
# v-component of current
band_num_u_current_if = list(range(10,30))
u_current_if = dict(zip(band_depth_if,band_num_u_current_if))

##################### lf ######################
band_depth_lf = [1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]
# Salinity
band_num_salinity_lf = list(range(73,94))
salinity_lf = dict(zip(band_depth_lf,band_num_salinity_lf))
# Water temperature
band_num_water_temp_lf = list(range(52,73))
water_temp_lf = dict(zip(band_depth_lf,band_num_water_temp_lf))
# v-component of current
band_num_v_current_lf = list(range(31,52))
v_current_lf = dict(zip(band_depth_lf,band_num_v_current_lf))
# v-component of current
band_num_u_current_lf = list(range(10,31))
u_current_lf = dict(zip(band_depth_lf,band_num_u_current_lf))

##################### lb ######################
band_depth_lb = [1,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,35,37,39,41,43,45,47,49,51,53,55]
# Salinity
band_num_salinity_lb = list(range(136,178))
salinity_lb = dict(zip(band_depth_lb,band_num_salinity_lb))
# Water temperature
band_num_water_temp_lb = list(range(94,136))
water_temp_lb = dict(zip(band_depth_lb,band_num_water_temp_lb))
# v-component of current
band_num_v_current_lb = list(range(52,94))
v_current_lb = dict(zip(band_depth_lb,band_num_v_current_lb))
# v-component of current
band_num_u_current_lb = list(range(10,52))
u_current_lb = dict(zip(band_depth_lb,band_num_u_current_lb))


fore_para_names = []