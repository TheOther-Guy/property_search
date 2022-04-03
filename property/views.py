
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts import HttpResponse
from django.template.context import RequestContext
from .models import Feature
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import django.contrib.messages as messages
from django.views.decorators.http import require_POST
import geopandas as gpd
import pandas as pd
import requests
import http.client, urllib.parse
import numpy as np
import re  #  8700 sunlit cove dr. St. Petersburg, FL
import json
from shapely.geometry import Point, MultiPoint, LineString, Polygon
import shapely
from shapely.geos import WKTReadingError
import folium
from folium import IFrame



# Create your views here.
def epa(request):
    m = folium.Map(location=[38.500000, -98.000000], zoom_start=5)
    folium.TileLayer('CartoDB positron', control=True).add_to(m)  # use folium to add alternative tiles
    #folium.LayerControl().add_to(m)  # use folium to add layer control
    m = m._repr_html_()
    context = {'m' : m}
    
    
    
    return render(request, 'epa.html', context)

def fema(request):
    
    m = folium.Map(location=[38.500000, -98.000000], zoom_start=5)
    folium.TileLayer('CartoDB positron', control=True).add_to(m)  # use folium to add alternative tiles
    #folium.LayerControl().add_to(m)  # use folium to add layer control
    m = m._repr_html_()
    context = {'m' : m}
    
    return render(request, 'fema.html', context)

def index(request):

    features = Feature.objects.all() # controling the template
    # from the back end
    
    return render(request, 'index.html', {'features':features})
    

    
def melissa(request):
    
    m = folium.Map(location=[38.500000, -98.000000], zoom_start=5)
    folium.TileLayer('CartoDB positron', control=True).add_to(m)  # use folium to add alternative tiles
    #folium.LayerControl().add_to(m)  # use folium to add layer control
    m = m._repr_html_()
    context = {'m' : m}
    
    data = {}
    if 'user_address' in request.GET:
        try:
            user_address = request.GET['user_address']
            sep = '&'
            base_url = "https://property.melissadata.net/v4/WEB/LookupProperty?"
            id_ = 'id=eSDChydmJdiUYj-c8V5aqV**nSAcwXpxhQ0PC2lXxuDAZ-**'
            patch_name = 't=test'
            cols = 'cols=GrpAll'
            format_ = 'format=JSON'

            full_address = 'ff='+ user_address

            url = base_url + id_ + sep + patch_name + sep + cols + sep + format_ + sep + full_address

            payload={}
            headers = {}

            response = requests.get(url, headers=headers, data=payload)

            requests_data = response.text

            data = json.loads(requests_data)
            final_request_data = pd.json_normalize(data['Records'])
            
            final_request_data.rename(columns={'Shape.WellKnownText':'geometry'}, inplace=True)
            
            # convert to geodataframe and do processing maybe will be raplaced with geodjango functins LATER !!!
            geometry = final_request_data['geometry'].map(shapely.wkt.loads) # mapping the geometry
            gdf_melissa = gpd.GeoDataFrame(final_request_data, crs=('WGS84'), geometry=geometry)
            gdf_melissa = gdf_melissa.replace("", np.nan) # replace empty strings with np.nan
            gdf_melissa = gdf_melissa.dropna(how='all', axis=1) # drop nan values
            gdf_melissa = gdf_melissa.to_crs('ESRI:102009') # convert the crs to metric to get segment length in meters
            melissa_exploded = gdf_melissa.explode(column='geometry', ignore_index=True) # exploding the geomtry to get segments
            melissa_exploded.geometry.simplify(1) # simplyfing to get rid of the additional points
            #final_request_data = final_request_data.to_html()
            # Facts about polygon outer vertices
            # - first vertex is the same as the last
            # - to get segments, ignore zero-th point (use it as from_point in next row)
            # create basic lists for creation of new dataframe
            indx = []  # for A1, A3
            sequ = []  # for seg order
            pxy0 = []  # from-point
            pxy1 = []  # to-point
            for ix,geom in zip(melissa_exploded.index, melissa_exploded.geometry):
                num_pts = len(geom.exterior.xy[0])
                #print(ix, "Num points:", num_pts)
                old_xy = []
                for inx, (x,y) in enumerate(zip(geom.exterior.xy[0],geom.exterior.xy[1])):
                    if (inx==0):
                        # first vertex is the same as the last
                        pass
                    else:
                        indx.append(ix)
                        sequ.append(inx)
                        pxy0.append(Point(old_xy))
                        pxy1.append(Point(x,y))
                    old_xy = (x,y)

            # Create new geodataframe
            melissa_segs  = gpd.GeoDataFrame({"poly_id": indx,
                            "vertex_id": sequ,
                            "fr_point": pxy0,
                            "to_point": pxy1}, crs='ESRI:102009')
            # Compute segment lengths
            # Note: seg length is Euclidean distance, ***not geographic***
            melissa_segs["seg_length"] = melissa_segs.apply(lambda row: row.fr_point.distance(row.to_point), axis=1)

            # creating the linestring column
            melissa_segs['line'] = melissa_segs.apply(lambda row: LineString([row['fr_point'], row['to_point']]), axis=1)
            # renaming line to geometry
            melissa_segs.rename(columns={'line':'geometry'}, inplace=True)
            # setting geometry as the geometry column
            melissa_segs = melissa_segs.set_geometry('geometry')
            # extracting nodes gdf dataframe columns
            nodes_df = melissa_segs[['poly_id','vertex_id','fr_point','to_point']]
            # ranming fr_point to geometry
            nodes_df.rename(columns={'fr_point':'geometry'}, inplace=True)
            # transforming pandas df to gdf
            nodes_gdf = gpd.GeoDataFrame(nodes_df, geometry='geometry', crs=melissa_segs.crs)

            melissa_segs.drop(columns=['fr_point','to_point'], inplace=True)

            melissa_segs.seg_length = melissa_segs.seg_length * 3.2808399

            melissa_segs.seg_length = round(melissa_segs.seg_length, 1)

            #html_df = final_request_data.to_html()

            lat = gdf_melissa['PropertyAddress.Latitude']
            lon = gdf_melissa['PropertyAddress.Longitude']

            m = folium.Map(location=[lat, lon], zoom_start=20)

            melissa_segs.explore(m=m,
                                color='blue')

            nodes_gdf.geometry.explore(m=m,
                    color='red'
                    )
            # dropping empty columns
            final_request_data = final_request_data.replace(["", 0], np.nan)
            final_request_data = final_request_data.dropna(how='all', axis=1)
            final_request_data = final_request_data.transpose()
            # getting the dataframe as a HTML table
            html = final_request_data.iloc[2:,:].to_html()
            #html = final_request_data.to_html()
            iframe = folium.IFrame(html=html, width=400, height=300)
            popup = folium.Popup(iframe, max_width=2650)
            folium.Marker([lat, lon], popup=popup).add_to(m)
            folium.TileLayer('CartoDB positron', control=True).add_to(m)  # use folium to add alternative tiles
            #folium.LayerControl().add_to(m)  # use folium to add layer control

            m = m._repr_html_()
            context = {'m' : m , 'html':html}

            # adding exception for the error when shape column is empty
        except WKTReadingError:
            print("Location is not found in our database...\n" "Try another address")
        

    return render(request, 'melissa.html', context)




def map(request):
    
    m = folium.Map(location=[38.500000, -98.000000], zoom_start=5)
    folium.TileLayer('CartoDB positron', control=True).add_to(m)  # use folium to add alternative tiles
    #folium.LayerControl().add_to(m)  # use folium to add layer control
    m = m._repr_html_()
    context = {'m' : m}
    
    return render(request, 'map.html', context)


def register(request):
    # this function demonistrate user registration
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already used')
                return redirect('register')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'User name already in use')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save();
                return redirect('Login')
        else:
            messages.info(request, 'Passwords do not match')
            return redirect('register')
    else:
        return render(request, 'register.html')

def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials is Invalid')
            return redirect ('Login')
    else:
        return render(request, 'login.html')
    
def Logout(request):
    logout(request)
    return redirect('/')




