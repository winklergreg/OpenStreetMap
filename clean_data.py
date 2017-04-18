import re

street_suite_num_re = re.compile(r'\#+[0-9]*$', re.IGNORECASE)
postcode_cdn_re = re.compile(r'^[A-Z]', re.IGNORECASE)
postcode_us_re = re.compile(r'^[0-9]')
whitespace_re = re.compile(r'\s\s+')
street_types = re.compile(r'\Z')
abbr_street_re = re.compile(r'(St.|St)$', re.IGNORECASE)
abbr_road_re = re.compile(r'(Rd.|Rd)$', re.IGNORECASE)
abbr_court_re = re.compile(r'(Ct)$', re.IGNORECASE)
abbr_parkway_re = re.compile(r'(Pkwy|Pky)$', re.IGNORECASE)
abbr_drive_re = re.compile(r'(Dr)$', re.IGNORECASE)
abbr_lane_re = re.compile(r'(Ln)$', re.IGNORECASE)
abbr_boulevard_re = re.compile(r'(Blvd)$', re.IGNORECASE)
abbr_avenue_re = re.compile(r'(Ave.|Ave)$', re.IGNORECASE)

def is_street_name(elem):
    return (elem == 'street')


def is_post_code(elem):
    return (elem == 'postcode')


def is_city(elem):
    return (elem == 'city')


def fix_saint_abbr(name):
    try:
        return re.sub(r'\A(St. |St )', 'Saint ', name)
    except:
        return name


def fix_city_names(city):
    try:
        city = re.sub(r'\S+(?: of )', '', city) #Remove the characters before a city name that include " of " 
        city = fix_saint_abbr(city)
        city = re.sub(r'(\,|\.)\D+', '', city) #Remove characters after and including a comma or decimal
    except:
        pass
    return city.title()


def check_postcode(postcode):
	postcode_length = len(postcode)
	if (postcode_length > 7 and postcode[2] == ' '):
		postcode = postcode[3:]

	is_usa = postcode_us_re.search(postcode)
	if is_usa:
		return fix_us_postcodes(postcode)
	else:
		return fix_cdn_postcodes(postcode)


def fix_cdn_postcodes(postcode):
    try:
        is_cdn = postcode_cdn_re.search(postcode)
        if is_cdn:
            if len(postcode) == 6:
                postcode = postcode[:3] + ' ' + postcode[3:]
            elif (len(postcode) == 7 and postcode[3] == '-'):
            	postcode = postcode[:3] + ' ' + postcode[4:]
    except:
        pass
    return postcode.upper()


def fix_us_postcodes(postcode):
    try:
        is_usa = postcode_us_re.search(postcode)
        if is_usa:
            if len(postcode) > 5:
                postcode = postcode[:5]    
    except:
        pass
    return postcode


def remove_extra_white_space(street_name):
    try:
        return re.sub(r'\s\s+', ' ', street_name)
    except:
        return street_name


def fix_street_types(street_name):
	try:
		if abbr_street_re.search(street_name):
			return abbr_street_re.sub('Street', street_name)
		elif abbr_road_re.search(street_name):
			return abbr_road_re.sub('Road', street_name)
		elif abbr_court_re.search(street_name):
			return abbr_court_re.sub('Court', street_name)
		elif abbr_parkway_re.search(street_name):
			return abbr_parkway_re.sub('Parkway', street_name)
		elif abbr_drive_re.search(street_name):
			return abbr_drive_re.sub('Drive', street_name)
		elif abbr_lane_re.search(street_name):
			return abbr_lane_re.sub('Lane', street_name)
		elif abbr_boulevard_re.search(street_name):
			return abbr_boulevard_re.sub('Boulevard', street_name)
		elif abbr_avenue_re.search(street_name):
			return abbr_avenue_re.sub('Avenue', street_name)
		else:
			return street_name	
	except:
		pass


def clean(elem):
    for el in elem:
    	el['value'] = remove_extra_white_space(el['value'])
        if is_street_name(el['key']):
            el['value'] = fix_saint_abbr(el['value']) 
            el['value'] = fix_street_types(el['value'])

        if is_post_code(el['key']):
            el['value'] = check_postcode(el['value'])
        
        if is_city(el['key']):
            el['value'] = fix_city_names(el['value'])
    
        el.update({'value': el['value']})

    return elem
    

if __name__ == '__main__':
    clean()