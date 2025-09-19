# This script visualizes school locations on an interactive map using Plotly.
# Run and view in browser.
# import necessary libraries
import json
import pandas as pd
import plotly.express as px

# -------------------
# Load JSON data
# -------------------
with open("data/school_data.json", "r") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# -------------------
# Extract lat/lon
# -------------------
df["lat"] = df["location_1"].apply(lambda x: float(x["latitude"]) if x else None)
df["lon"] = df["location_1"].apply(lambda x: float(x["longitude"]) if x else None)

# -------------------
# Build map
# -------------------
fig = px.scatter_mapbox(
    df,
    lat="lat",
    lon="lon",
    hover_name="campus_name",
    hover_data=["campus_address", "grade_range", "category"],
    color="grade_range",   # color by school category (e.g. PreK, Elementary, etc.)
    zoom=11,
    height=700
)

# Add custom hover info
fig.update_traces(
    customdata=df[["campus_name", "campus_address", "grade_range", "category"]],
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>" +   # campus_name
        "📍 %{customdata[1]}<br>" +      # campus_address
        "🎓 Grades: %{customdata[2]}<br>" + # grade_range
        "🏷️ Category: %{customdata[3]}<extra></extra>"  # category
    )
)

fig.update_layout(
    mapbox_style="carto-positron",  # clean, leaflet-like style
    margin={"r":0,"t":0,"l":0,"b":0}
)

fig.show(renderer="browser")
