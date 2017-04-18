# OpenStreetMap Data Case Study
By Gregory Winkler

**Map Area**
*Buffalo-Niagara Falls, NY, United States*

This map is the area where I was raised and a region that is still important to me. This area was not a popular extract on Metro Extracts, so I am curious to see what the database reveals for the region.


##**Problematic areas with the Map Data**

After downloading a sample of the data, a few issues were discovered that should be cleaned up before taking a deeper dive.

* Inconsistent Postal Codes: Occasional use of the extra 4 digit code following the standard 5 digits.  Canadian 6 digit postal codes are represented in the dataset due to its proximity of the region, some of which need to be reformatted.  
* Use of Abbreviations for the word 'Saint'
* Inconsistent City Naming Conventions: Frequent use of "City of ..." or "Town of ...".  While this may not be incorrect information, it would be better to store it in a separate field. Some entries use the key, "place", to store this information.
* A '?' Appears as a City Name in the Data.
* Excessive Whitespace for Street Names


**Inconsistent Postal Codes**
Although there were not many postal codes consisting of more than the standard 5 digits, I decided to make the data consistent and strip any digits after the first 5.   Note that an extra step was included here to only apply this stripping to US postal codes. Canadian postal codes were addressed in the next step.

	def fix_us_postcodes(postcode):
	    try:
	        is_usa = postcode_us_re.search(postcode)
        	if is_usa:
	            if len(postcode) > 5:
	                postcode = postcode[:5]    
	    except:
	        pass
	    return postcode


Canadian postal codes show inconsistencies where some fail to include a single space after the first three characters.

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

A query of the postcodes does show what is most likely a human input error.  There is a single postcode with a value of 13201.  This region should only contain postcodes starting with 14xxx.  Given that this is likely an error I did a quick query to get the other data in the node_tags table for this ID.

	sqlite> SELECT * FROM node_tags 
			WHERE Id IN
			(SELECT Id FROM node_tags WHERE key='postcode' and value='13201');

The other data points show that this is a Tops fuel store on Niagara Street in Buffalo, NY.  I did a quick google search for this additional data and found that there is a Tops at this address with a postcode of 14201.  It would appear that the user who submitted this tag simply entered it incorrectly.  

**Use of Abbreviations for the word 'Saint'**
Many street and city names in the dataset begin their name with the word "saint".  However, this word is represented by three versions; 'Saint', 'St.', and 'St'.  As a result, the data in its current form does will not group these together despite the fact that they all represent the same location.  The below code was implemented to change the abbreviations for 'Saint' to spell out the full word. This changes an occurrence of 'St.' and 'St' when found at the beginning of a street name.

	def fix_saint_abbr(name):
	    try:
	        return re.sub(r'\A(St. |St )', 'Saint ', name)
	    except:
	        return name


**Inconsistent City Naming Conventions**
Many of the city names include a reference to its type of place. For example, the 'type' may be "Town of ..." which would be more appropriately captured in the 'place' key. Any references to a substring consisting of "*TYPE of* ..." have been stripped from the city name.  In addition, a call is made to a function used earlier to replace abbreviations for the word "Saint".  Lastly, there was a need to remove all occurrences of a decimal or comma and the subsequent characters.  These additional characters were representing the state of the city.

	def fix_city_names(city):
	    try:
	        city = re.sub(r'\S+(?: of )', '', city)
	        city = fix_saint_abbr(city)
	        city = re.sub(r'(\,|\.)\D+', '', city) #Remove characters after and including a comma or decimal
	    except:
	        pass
	    return city.title()


**A '?' for a City Name**
As part of an audit to review the city names that are in the dataset, I noticed a modest number of results with a city name equivalent to '?'.  This is obviously not a valid city name so it made sense to dig a little deeper into these data points.  

	sqlite>	SELECT * FROM Nodes 
			WHERE Id IN (SELECT Id FROM Node_Tags WHERE key='city' AND value='?');

After mapping the latitude and longitude coordinates, it shows that these data points take me to Rock Point Provincial Park. According to the Park's website, it is located in the city of Dunnville, ON.  It was also interesting to note that the Park shows up as a separate city name.   

I chose to delete all records associated with the '?' city name as further analysis showed that these entries do not provide any meaningful information.  

	sqlite> DELETE FROM node_tags
			WHERE key='city' and value='?';


**Excessive White Space in Street Names**
There are some examples where more than a single white space character is entered between words in street names.  This is causing some streets to be listed twice since the extra space creates a mismatch.

	def remove_extra_white_space(street_name):
	    try:
	        return re.sub(r'\s\s+', ' ', street_name)
	    except:
	        return street_name

Separately, I cleaned up the street types that were abbreviated.  

	abbr_street_re = re.compile(r'(St.|St)$', re.IGNORECASE)
	abbr_road_re = re.compile(r'(Rd.|Rd)$', re.IGNORECASE)
	abbr_court_re = re.compile(r'(Ct)$', re.IGNORECASE)
	abbr_parkway_re = re.compile(r'(Pkwy|Pky)$', re.IGNORECASE)
	abbr_drive_re = re.compile(r'(Dr)$', re.IGNORECASE)
	abbr_lane_re = re.compile(r'(Ln)$', re.IGNORECASE)
	abbr_boulevard_re = re.compile(r'(Blvd)$', re.IGNORECASE)
	abbr_avenue_re = re.compile(r'(Ave.|Ave)$', re.IGNORECASE)

	def fix_street_types(street_name):
		try:
			if abbr_street_re.search(street_name):
				print abbr_street_re.sub('Street', street_name)
			elif abbr_road_re.search(street_name):
				print abbr_road_re.sub('Road', street_name)
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


##**Data Overview**

This section contains basic statistics about the dataset, including the SQL queries used to retrieve the information.


**File Sizes**

	buffalo-niagara-falls_new-york.osm ... 293 MB
	buffalo.db ........................... 203 MB
	nodes.csv ............................ 99 MB
	nodes_tags.csv ....................... 17 MB
	ways.csv ............................. 10 MB
	ways_tags.csv ........................ 28 MB
	ways_nodes.csv ....................... 32 MB

**Number of Nodes**

	sqlite> SELECT COUNT(*) FROM nodes;

1257033

**Number of Ways**

	sqlite> SELECT COUNT(*) FROM ways;

179986

**Number of Unique Users**

	sqlite> SELECT COUNT(DISTINCT(n.Uid))
			FROM (SELECT Uid FROM nodes UNION ALL
				SELECT Uid FROM ways) n;

1085

**Top 10 Contributing Users**

	sqlite> SELECT n.user, COUNT(*) as count
			FROM (SELECT user FROM nodes UNION ALL
				SELECT user FROM ways) n
			GROUP BY n.user
			ORDER BY count DESC LIMIT 10;

	andrewpmk ............. 305968
	woodpeck_fixbot ....... 250092
	MickeyCarter .......... 239163
	jdmonin ............... 81015
	cl94 .................. 54649
	RussNelson ............ 51829
	a_white ............... 47903
	fx99 .................. 20818
	Hwyfan ................ 17631
	chdr .................. 15109

**Number of Users Appearing Only Once**

	sqlite> SELECT COUNT(*)
			FROM (SELECT n.user, COUNT(*) as count
				FROM (SELECT user FROM nodes UNION ALL
					SELECT user FROM ways) n
				GROUP BY n.user
				HAVING count=1) u;

223


##**Additional Ideas**


**Top 10 City Tags**

	sqlite> SELECT tags.value, count(*) as count
			FROM (SELECT * FROM node_tags UNION ALL
				SELECT * FROM way_tags) tags
			WHERE key='name'
			GROUP BY tags.value
			ORDER BY count DESC LIMIT 10;

	Saint Catharines ...... 17010
	Niagara Falls ......... 14931
	Fort Erie ............. 11089
	Welland ............... 7655
	Lincoln ............... 7025
	Niagara-On-The-Lake ... 6468
	West Lincoln .......... 6417
	Pelham ................ 5036
	Port Colborne ......... 4894
	Grimbsy ............... 4701

Its obvious from the results that there is a lot of data missing from the Buffalo region.  The data is predominantly cities in Canada, which geographically represents a small area of the map.  In fact, Buffalo doesn't show up until #15 with a count of 433.  Its likely that the top contributors for this region are Canadian users and not concerned with extending their mapping across the border into the United States.  Therefore, the Buffalo region would benefit greatly from additional users contributing to the map.

**Top 10 Name Node Tags, Excluding Schools**

	sqlite> SELECT value, count(*) as count
			FROM node_tags
			WHERE key='name' and value NOT LIKE "%School%"
			GROUP BY value
			ORDER BY count DESC LIMIT 10;

	Tim Hortons ................ 37
	Subway ..................... 33
	McDonalds .................. 28
	Sunoco ..................... 16
	Tops ....................... 16
	7-Eleven ................... 14
	First Presbyterian Church .. 14
	Wendy's .................... 14
	First Baptist Church ....... 13
	Dunkin' Donuts ............. 11

Its interesting to see Tim Hortons is the most frequent here but not too surprising given its popularity in the region.  Also interesting to note that 5 of the top 10 are fast-food locations.

**Top 5 Amenity Node Tags**

	sqlite> SELECT value, count(*) as count
			FROM node_tags
			WHERE key='amenity'
			GROUP BY value
			ORDER BY count DESC LIMIT 5;

	school ................. 845
	place_of_worship ....... 506
	grave_yard ............. 370
	restaurant ............. 331
	parking ................ 323

**Idea to Improve the Map**
After reviewing the data and the city count queried above, the map might see significant improvements if users were made aware of significant shortcomings in certain regions of the map. This might encourage users to contribute to that region if they know it has significant room for improvement. 

##**Conclusion**

The data revealed a lot of information, but it was disappointing to see that the brief area of Canada that is part of this map has significantly more information than the city of Buffalo and its suburbs.  However, aside from a few issues, it is encouraging to know that the data is quite clean.  It would be great to see significant contributions to the Buffalo region whether by a GPS bot or individual contributions.
