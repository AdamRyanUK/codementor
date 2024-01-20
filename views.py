import xarray as xr
import io
from django.shortcuts import render
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from matplotlib import colors as mcolors
import os
import glob
import datetime
import base64
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from snow_forecast.models import Resort
from django.conf import settings
from scipy.spatial.distance import cdist

def generate_snow_map(url, filename, title):
    # Download the file using requests
    response = requests.get(url)

    # Save the content to a local file
    with open(filename, 'wb') as f:
        f.write(response.content)

    # Open the local file using xarray
    ds = xr.open_dataset(filename)

    # Extract latitude, longitude, and data values
    latitude = ds['latitude'].values
    longitude = ds['longitude'].values
    data_values = ds['unknown'].values*100
    data_values[data_values == 0] = np.nan

    # Create a map projection centered on the U.S.
    projection = ccrs.LambertConformal(central_longitude=-100, central_latitude=40)

    # Create a figure and axis with the specified projection
    fig, ax = plt.subplots(subplot_kw={'projection': projection}, figsize=(9, 5))

    # Plot the data on the map using the custom colormap with boundaries
    colors = ['#e4eef5', '#bdd7e7', '#6baed6', '#3182bd', '#08519c',
              '#082694', '#ffff96', '#ffc400', '#ff8700', '#db1400',
              '#9e0000', '#690000', '#2b002e', '#4c0073']

    upper_bound = 100
    bounds = [0, 0.1, 1, 2, 3, 4, 6, 8, 12, 18, 24, 30, 36, 48, upper_bound]

    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(bounds, cmap.N, clip=False)

    im = ax.pcolormesh(longitude, latitude, data_values, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm)

    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    ax.add_feature(cfeature.STATES, linewidth=0.5)

    # Set the land area to white and the sea area to transparent
    land_color = '#ffffff'  # White
    # Set the ocean area to partly transparent
    ocean_color = (1, 1, 1, 0.6)  # Partly transparent

    ax.add_feature(
        cfeature.COASTLINE,
        facecolor='none',  # Make the coastline transparent
        edgecolor='black',
        linewidth=0.5,
        alpha=0.6  # Set the alpha value for transparency
    )

    ax.add_feature(
        cfeature.LAND,
        facecolor=land_color,
        edgecolor='black',
        linewidth=0.5
    )

    ax.add_feature(
        cfeature.OCEAN,
        facecolor=ocean_color,
        edgecolor='none',  # Make the ocean boundary transparent
    )

    # Add a colorbar
    cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02, boundaries=bounds, ticks=bounds[:-1], shrink=0.65)
    cbar.set_label('Inches of New Snow')

    # Set title and save the plot to a BytesIO object
    plt.title(title)
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png',  bbox_inches='tight', transparent=True)
    buffer.seek(0)
    plt.close(fig)

    # Convert the plot to base64 encoding
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')

    # Delete the grib file
    os.remove(filename)

    idx_pattern = f"{filename}.*.idx"
    for idx_file in glob.glob(idx_pattern):
        try:
            if os.path.exists(idx_file):
                os.remove(idx_file)
        except Exception as e:
            print(f"Error deleting {idx_file}: {e}")

    return graphic
def snowdepth(request):
       
    # Get the current date in the required format
    current_date = datetime.datetime.now()
    yyyymm = current_date.strftime('%Y%m')
    dd = current_date.strftime('%d')
    current_date_str = current_date.strftime('%Y-%m-%d')


    # Generate the 24-hour snow depth map
    url_24hr = f'https://www.nohrsc.noaa.gov/snowfall/data/{yyyymm}/sfav2_CONUS_24h_{yyyymm}{dd}00_grid184.grb2'
    filename_24hr = f'snow_depth_map_24hr_{yyyymm}.grib'
    title_24hr = f'24-Hour Snow Depth Map {current_date_str}'
    graphic_24hr = generate_snow_map(url_24hr, filename_24hr, title_24hr)

    # Generate the 72-hour snow depth map
    url_72hr = f'https://www.nohrsc.noaa.gov/snowfall/data/{yyyymm}/sfav2_CONUS_72h_{yyyymm}{dd}00_grid184.grb2'
    filename_72hr = f'snow_depth_map_72hr_{yyyymm}.grib'
    title_72hr = f'72-Hour Snow Depth Map {current_date_str}'
    graphic_72hr = generate_snow_map(url_72hr, filename_72hr, title_72hr)

    # Save the graphics to static files
    static_dir = os.path.join(BASE_DIR, 'sleety', 'static', 'images', 'snow_depth_maps')
    os.makedirs(static_dir, exist_ok=True)
    static_file_24hr = os.path.join(static_dir, 'snow_depth_map_24hr.png')
    static_file_72hr = os.path.join(static_dir, 'snow_depth_map_72hr.png')
    with open(static_file_24hr, 'wb') as f:
        f.write(base64.b64decode(graphic_24hr))
    with open(static_file_72hr, 'wb') as f:
        f.write(base64.b64decode(graphic_72hr))

 

    return render(request, 'snowdepth.html', {graphic_24hr: graphic_24hr, graphic_72hr: graphic_72hr})
