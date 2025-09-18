import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import db_pool
import configparser
from datetime import datetime
from rich import print
import geoip2.database
from pathlib import Path

# Create a ConfigParser object and read settings
config = configparser.ConfigParser()
config.read("config.properties")

# Fetch settings
backend_url = config.get("settings", "backend_url")
version = config.get("settings", "version")


# GeoIP configuration
# Sign up for a free account at MaxMind: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
# Download the GeoLite2-Country database and place it in the same directory as this script
GEOIP_DB_PATH = "GeoLite2-Country.mmdb"


def fetch_geolocation(ip_address):
    try:
        if not Path(GEOIP_DB_PATH).exists():
            return "Database not found"

        with geoip2.database.Reader(GEOIP_DB_PATH) as reader:
            response = reader.country(ip_address)
            return response.country.name
    except geoip2.errors.AddressNotFoundError:
        return "Unknown"
    except Exception as e:
        return f"Error: {str(e)}"


def log_request(client_ip, source="General"):
    country = fetch_geolocation(client_ip)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] Source: {source}, IP: {client_ip}, Country: {country}"
    print(log_message)

# Define the dashboard interface
with gr.Blocks(theme=gr.themes.Ocean()) as demo:
    demo.title = "Sparrow Analytics Dashboard"

    # Log initial page load
    @demo.load(api_name=False)
    def on_page_load(request: gr.Request):
        log_request(request.client.host, "Dashboard Page Load")

    # Combine CSS and responsive messaging for both desktop and mobile
    # responsive_layout = gr.HTML("""
    # <style>
    #     /* Mobile-specific styles */
    #     @media (max-width: 767px) {
    #         #period-selector,
    #         #document-size-container,
    #         #model-usage-container,
    #         #timeline-container,
    #         #countries-container,
    #         #unique-users-container,
    #         .plotly-chart {
    #             display: none !important;
    #         }
    #
    #         /* Force metrics container to vertical layout on mobile */
    #         #metrics-container {
    #             flex-direction: column !important;
    #             gap: 8px !important;
    #             margin-top: 5px !important;
    #         }
    #
    #         /* Stack metrics vertically on mobile */
    #         #metrics-container > div {
    #             flex: none !important;
    #             width: 100% !important;
    #             margin-bottom: 8px !important;
    #         }
    #
    #         /* Reduce footer spacing on mobile */
    #         .footer-container {
    #             margin-top: 15px !important;
    #         }
    #     }
    #
    #     /* Make sure the footer is always visible regardless of screen size */
    #     .footer-markdown p {
    #         text-align: center;
    #     }
    #
    #     .footer-markdown hr {
    #         margin: 20px 0 10px 0;
    #     }
    # </style>
    # """)

    # Time period selector
    with gr.Row(elem_id="period-selector"):
        period_selector = gr.Radio(
            label="Time Period",
            choices=["1week", "2weeks", "1month", "6months", "all"],
            value="1week",
            interactive=True
        )

    # Key metrics at the top (HTML-based for better styling)
    with gr.Row(elem_id="metrics-container"):
        metrics_html = gr.HTML()

    # First row - HTML visualizations for document size and model usage
    with gr.Row():
        with gr.Column(elem_id="document-size-container"):
            inference_pages_html = gr.HTML(label="Document Size Performance")
        with gr.Column(elem_id="model-usage-container"):
            model_usage_html = gr.HTML(label="Model Usage")

    # Second row - Inference events timeline using Plotly
    with gr.Row(elem_id="timeline-container", visible=True):
        daily_events_plot = gr.Plot(label="Inference Events Timeline", elem_classes="plotly-chart")

    # Third row - Country distribution (split into two columns)
    with gr.Row(elem_id="countries-container"):
        with gr.Column():
            country_html = gr.HTML(label="Inference Requests by Country")
        with gr.Column(elem_id="unique-users-container"):
            unique_users_html = gr.HTML(label="Unique Users by Country")


    # Function to process data and generate visualizations
    def update_dashboard(period):
        # Default to "1week" if period is None or invalid
        period = period or "1week"
        # Fetch data from database
        logs = db_pool.get_inference_logs(period)
        unique_users_data = db_pool.get_unique_users_by_country(period)

        # If no data is available, return empty charts
        if not logs:
            empty_text = "No data available"
            empty_html = "<div style='text-align:center; padding: 20px;'>No data available</div>"
            empty_plot = None
            empty_metrics = """
            <div style="display: flex; justify-content: center; align-items: center; height: 100px; border-radius: 12px; background-color: #f8f9fa; border: 1px dashed #dee2e6;">
                <p style="color: #6c757d; font-size: 16px;">No data available for the selected time period</p>
            </div>
            """
            return [empty_metrics, empty_html, empty_html, empty_plot, empty_html, empty_html]

        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(logs)

        # Calculate summary metrics
        total_count = len(df)
        success_count = df['inference_duration'].notna().sum()
        failure_count = total_count - success_count
        success_percentage = (success_count / total_count * 100) if total_count > 0 else 0

        # Calculate average duration
        avg_duration = df['inference_duration'].mean() if 'inference_duration' in df.columns else 0

        # Get top model info
        friendly_name = "No data"
        top_model_count = 0
        if 'model_name' in df.columns and not df['model_name'].empty:
            model_counts = df['model_name'].value_counts()
            if not model_counts.empty:
                top_model_name = model_counts.index[0]
                top_model_count = model_counts.iloc[0]

                # Replace model names with user-friendly names
                friendly_name = "Standard model" if "Mistral" in top_model_name else "Advanced model" if "Qwen" in top_model_name else top_model_name

        # Format key metrics as HTML with id attributes for JavaScript targeting
        metrics_html_content = f"""
        <div id="metrics-container" style="display: flex; justify-content: space-between; gap: 16px; width: 100%; padding: 8px 0;">
            <div style="flex: 1; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); padding: 16px; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background-color: #4ecdc4; display: flex; justify-content: center; align-items: center; margin-right: 12px;">
                        <span style="color: white; font-size: 14px;">📊</span>
                    </div>
                    <h3 style="margin: 0; color: #343a40; font-size: 14px; font-weight: 500;">Total Inferences</h3>
                </div>
                <p style="margin: 0; font-size: 24px; font-weight: 600; color: #212529;">{total_count:,}</p>
            </div>

            <div style="flex: 1; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); padding: 16px; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background-color: #56b4e9; display: flex; justify-content: center; align-items: center; margin-right: 12px;">
                        <span style="color: white; font-size: 14px;">✓</span>
                    </div>
                    <h3 style="margin: 0; color: #343a40; font-size: 14px; font-weight: 500;">Success Rate</h3>
                </div>
                <p style="margin: 0; font-size: 24px; font-weight: 600; color: #212529;">{success_percentage:.1f}%</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #6c757d;">({success_count:,} successful, {failure_count:,} failed)</p>
            </div>

            <div style="flex: 1; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); padding: 16px; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background-color: #8da0cb; display: flex; justify-content: center; align-items: center; margin-right: 12px;">
                        <span style="color: white; font-size: 14px;">⏱️</span>
                    </div>
                    <h3 style="margin: 0; color: #343a40; font-size: 14px; font-weight: 500;">Avg. Duration</h3>
                </div>
                <p style="margin: 0; font-size: 24px; font-weight: 600; color: #212529;">{avg_duration:.2f}s</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #6c757d;">per inference</p>
            </div>

            <div style="flex: 1; background: linear-gradient(135deg, #f8f9fa, #e9ecef); border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); padding: 16px; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid rgba(0,0,0,0.04);">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <div style="width: 28px; height: 28px; border-radius: 50%; background-color: #66c2a5; display: flex; justify-content: center; align-items: center; margin-right: 12px;">
                        <span style="color: white; font-size: 14px;">🔍</span>
                    </div>
                    <h3 style="margin: 0; color: #343a40; font-size: 14px; font-weight: 500;">Most Used Model</h3>
                </div>
                <p style="margin: 0; font-size: 24px; font-weight: 600; color: #212529;">{friendly_name}</p>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #6c757d;">({top_model_count:,} uses)</p>
            </div>
        </div>
        """

        # Generate Plotly chart for Inference Events
        events_plot = None
        if all(col in df.columns for col in ['log_date', 'inference_duration', 'page_count']):
            # Filter out rows with null duration
            events_df = df.dropna(subset=['inference_duration', 'page_count'])

            # Convert timestamp to datetime if it's not already
            if not pd.api.types.is_datetime64_any_dtype(events_df['log_date']):
                events_df['log_date'] = pd.to_datetime(events_df['log_date'])

            # Sort by date
            events_df = events_df.sort_values('log_date')

            # No need to group by day - we want individual inference events
            # Use the raw data points directly for visualization

            # Create a more readable page count description
            events_df['page_description'] = events_df['page_count'].astype(str) + " page" + \
                                            (events_df['page_count'] > 1).astype(str).str.replace('True',
                                                                                                  's').str.replace(
                                                'False', '')

            # Create a custom hover template
            hover_template = (
                    "<b>%{customdata[0]}</b><br>" +
                    "Date: %{x|%Y-%m-%d %H:%M:%S}<br>" +
                    "Duration: %{y:.2f} seconds<br>" +
                    "Pages: %{customdata[1]}<br>" +
                    "<extra></extra>"  # Hide secondary box
            )

            # Create Plotly scatter plot directly using the individual inference events
            fig = go.Figure()

            # Get unique page counts for color mapping
            unique_page_counts = sorted(events_df['page_count'].unique())

            # Create a custom color palette with soft, modern, harmonious colors
            # These colors are chosen to be visually pleasing and work well together
            soft_palette = [
                '#4ecdc4',  # Soft teal
                '#56b4e9',  # Soft blue
                '#8da0cb',  # Periwinkle
                '#5e6ebe',  # Muted blue-purple
                '#a6cee3',  # Light blue
                '#66c2a5',  # Mint
                '#3288bd',  # Medium blue
                '#7fcdbb',  # Seafoam
                '#67a9cf',  # Sky blue
                '#6baed6',  # Steel blue
            ]

            # If we have more unique page counts than colors, repeat colors
            if len(unique_page_counts) > len(soft_palette):
                # Create additional colors by repeating the palette
                soft_palette = soft_palette * (len(unique_page_counts) // len(soft_palette) + 1)

            colors = soft_palette[:len(unique_page_counts)]

            # Add trace for each page count to control the legend
            for i, page_count in enumerate(unique_page_counts):
                color_idx = i % len(colors)
                page_data = events_df[events_df['page_count'] == page_count]

                fig.add_trace(go.Scatter(
                    x=page_data['log_date'],
                    y=page_data['inference_duration'],
                    mode='markers',
                    name=f"{page_count} page{'s' if page_count > 1 else ''}",
                    marker=dict(
                        size=page_data['page_count'] * 2,  # Reduced size multiplier from 4 to 2
                        sizemin=4,  # Reduced minimum size from 6 to 4
                        sizemode='area',
                        sizeref=2. * max(events_df['page_count']) / (20. ** 2),
                        # Adjusted scale factor for smaller points
                        color=colors[color_idx],
                        opacity=0.7,  # Added some transparency to reduce visual clutter
                        line=dict(width=0.5, color='DarkSlateGrey')  # Thinner border line
                    ),
                    customdata=list(zip(
                        ["Inference #" + str(i + 1) for i in range(len(page_data))],  # Custom label
                        page_data['page_description']
                    )),
                    hovertemplate=hover_template
                ))

            # Customize the layout
            fig.update_layout(
                title='Inference Events by Duration and Page Count',
                xaxis_title='Date & Time',
                yaxis_title='Inference Duration (seconds)',
                legend_title='Document Size',
                hovermode='closest',
                height=450,
                margin=dict(l=50, r=20, t=50, b=50),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    itemsizing='constant',  # Make all legend items a constant size
                    itemwidth=30,  # Set the width of legend items
                    itemclick=False,  # Disable item clicking to prevent toggling
                    itemdoubleclick=False  # Disable double-clicking to prevent toggling
                )
            )

            # Improve axis formatting
            fig.update_xaxes(
                tickformat="%m/%d\n%H:%M",  # Show month/day and hour/minute
                tickangle=-45,
                gridcolor='lightgray'
            )

            # Add range slider for time navigation
            fig.update_xaxes(
                rangeslider_visible=True,
                rangeslider_thickness=0.05
            )

            events_plot = fig
        else:
            # Return an empty plot
            events_plot = None

        # 2. Average Inference Duration by Page Count (HTML/CSS visualization)
        duration_html = ""
        if all(col in df.columns for col in ['inference_duration', 'page_count']):
            # Filter out rows with null duration
            duration_df = df.dropna(subset=['inference_duration'])

            # Group by page count and calculate average duration
            avg_by_page = duration_df.groupby('page_count')['inference_duration'].mean().reset_index()

            # Sort by page count
            avg_by_page = avg_by_page.sort_values('page_count')

            # Add page label with correct plurality
            avg_by_page['page_label'] = avg_by_page['page_count'].astype(str) + " page" + (
                    avg_by_page['page_count'] > 1).astype(str).str.replace('True', 's').str.replace('False', '')

            # Get the maximum duration for scaling the bars
            max_duration = avg_by_page['inference_duration'].max()

            # Create HTML for the visualization
            html = """
            <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
              <h3 style="margin-top: 0; margin-bottom: 15px; color: #333;">Average Inference Duration by Document Size</h3>
              <div style="display: flex; flex-direction: column; gap: 12px; max-width: 100%;">
            """

            # Create entry for each page count
            for _, row in avg_by_page.iterrows():
                duration = row['inference_duration']
                percent_width = min(95, (duration / max_duration) * 95) if max_duration > 0 else 0

                html += f"""
                <div style="display: flex; align-items: center; width: 100%;">
                  <div style="min-width: 80px; width: 80px; font-weight: 500; color: #444;">{row['page_label']}</div>
                  <div style="flex-grow: 1; display: flex; align-items: center; width: calc(100% - 80px);">
                    <div style="height: 18px; width: {percent_width}%; background-color: #1abc9c; border-radius: 4px;"></div>
                    <span style="margin-left: 10px; white-space: nowrap; color: #555; font-size: 14px;">{duration:.2f} seconds</span>
                  </div>
                </div>
                """

            html += """
              </div>
              <div style="margin-top: 15px; font-size: 13px; color: #777;">
                Based on {count} successful inferences
              </div>
            </div>
            """.format(count=len(duration_df))

            duration_html = html
        else:
            duration_html = "<div style='text-align:center; padding: 20px;'>No duration data available</div>"

        # 3. Country Distribution as HTML/CSS visualization with improved scrolling
        country_html_content = ""
        if 'country_name' in df.columns:
            # Get counts of unique countries
            country_counts = df['country_name'].value_counts().reset_index()
            country_counts.columns = ['country', 'count']

            # Calculate total for percentages
            total = country_counts['count'].sum()
            country_counts['percentage'] = (country_counts['count'] / total * 100).round(1)

            # First sort by country name alphabetically (secondary sort)
            country_counts = country_counts.sort_values('country')

            # Then sort by count in descending order (primary sort)
            # This ensures countries with the same count will be ordered alphabetically
            country_counts = country_counts.sort_values(['count', 'country'], ascending=[False, True])

            # Get the maximum count for scaling the bars
            max_count = country_counts['count'].max()

            # The number of visible countries without scrolling (approximately)
            visible_without_scroll = 10
            total_countries = len(country_counts)

            # Create HTML for the visualization
            html = """
            <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
              <h3 style="margin-top: 0; margin-bottom: 15px; color: #333;">Inference Requests by Country</h3>

              <!-- If there are more countries than can be displayed, show scroll indicator -->
              {scroll_indicator}

              <div style="max-height: 350px; overflow-y: auto; padding-right: 10px; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.05); border-radius: 6px; padding: 10px;">
                <div style="display: flex; flex-direction: column; gap: 8px; max-width: 100%;">
            """.format(
                scroll_indicator=f"""
                <div style="margin-bottom: 8px; font-size: 13px; color: #555; display: flex; align-items: center;">
                    <span style="margin-right: 5px;">Showing all {total_countries} countries</span>
                    <span style="color: #1abc9c; font-size: 18px;">↓</span>
                    <span style="color: #777; font-style: italic; margin-left: 5px;">Scroll to see more</span>
                </div>
                """ if total_countries > visible_without_scroll else ""
            )

            # Create entry for each country
            for _, row in country_counts.iterrows():
                percent_width = min(95, (row['count'] / max_count) * 95) if max_count > 0 else 0

                # Use the same green color as in the Average Inference Duration chart (#1abc9c)
                # Apply opacity variations based on the percentage for visual interest
                opacity = min(1.0, 0.6 + (row['percentage'] / 100 * 0.4))  # ranges from 0.6 to 1.0 based on percentage

                html += f"""
                <div style="display: flex; align-items: center; width: 100%;">
                  <div style="min-width: 150px; width: 150px; font-weight: 500; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{row['country']}">{row['country']}</div>
                  <div style="flex-grow: 1; display: flex; align-items: center; width: calc(100% - 150px);">
                    <div style="height: 16px; width: {percent_width}%; background-color: rgba(26, 188, 156, {opacity}); border-radius: 4px;"></div>
                    <span style="margin-left: 10px; white-space: nowrap; color: #555; font-size: 14px;">{row['count']:,} ({row['percentage']}%)</span>
                  </div>
                </div>
                """

            html += """
                </div>
              </div>
              <div style="display: flex; justify-content: space-between; font-size: 13px; color: #777;">
                <div>Based on {count} total inferences</div>
                <div>{num_countries} countries total</div>
              </div>
            </div>
            """.format(count=total, num_countries=len(country_counts))

            country_html_content = html
        else:
            country_html_content = "<div style='text-align:center; padding: 20px;'>No country data available</div>"

        # NEW: 4a. Unique Users by Country chart
        unique_users_html_content = ""
        if unique_users_data:
            # Convert to DataFrame
            unique_users_df = pd.DataFrame(unique_users_data)

            # Calculate total unique users for percentages
            total_unique = unique_users_df['unique_users'].sum() if 'unique_users' in unique_users_df.columns else 0

            if total_unique > 0:
                # Add percentage column
                unique_users_df['percentage'] = (unique_users_df['unique_users'] / total_unique * 100).round(1)

                # First sort by country name alphabetically (secondary sort)
                unique_users_df = unique_users_df.sort_values('country_name')

                # Then sort by unique_users count in descending order (primary sort)
                # This ensures countries with the same count will be ordered alphabetically
                unique_users_df = unique_users_df.sort_values(['unique_users', 'country_name'], ascending=[False, True])

                # Get max count for scaling
                max_unique = unique_users_df['unique_users'].max()

                # The number of visible countries without scrolling (approximately)
                visible_without_scroll = 10
                total_countries = len(unique_users_df)

                # Create HTML for the visualization with the same style as country_html
                html = """
                <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
                  <h3 style="margin-top: 0; margin-bottom: 15px; color: #333;">Unique Users by Country</h3>

                  <!-- If there are more countries than can be displayed, show scroll indicator -->
                  {scroll_indicator}

                  <div style="max-height: 350px; overflow-y: auto; padding-right: 10px; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.05); border-radius: 6px; padding: 10px;">
                    <div style="display: flex; flex-direction: column; gap: 8px; max-width: 100%;">
                """.format(
                    scroll_indicator=f"""
                    <div style="margin-bottom: 8px; font-size: 13px; color: #555; display: flex; align-items: center;">
                        <span style="margin-right: 5px;">Showing all {total_countries} countries</span>
                        <span style="color: #9b59b6; font-size: 18px;">↓</span>
                        <span style="color: #777; font-style: italic; margin-left: 5px;">Scroll to see more</span>
                    </div>
                    """ if total_countries > visible_without_scroll else ""
                )

                # Create entry for each country
                for _, row in unique_users_df.iterrows():
                    country_name = row['country_name']
                    unique_count = row['unique_users']
                    percentage = row['percentage']
                    percent_width = min(95, (unique_count / max_unique) * 95) if max_unique > 0 else 0

                    # Calculate a color based on the percentage (higher = more saturated)
                    # Use a different hue (purple) to distinguish from the Inference Requests chart
                    hue = 270  # Purple hue
                    saturation = min(80, 30 + (percentage * 2))  # Increase saturation with percentage
                    lightness = max(40, 70 - (percentage * 1.5))  # Decrease lightness with percentage

                    html += f"""
                    <div style="display: flex; align-items: center; width: 100%;">
                      <div style="min-width: 150px; width: 150px; font-weight: 500; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{country_name}">{country_name}</div>
                      <div style="flex-grow: 1; display: flex; align-items: center; width: calc(100% - 150px);">
                        <div style="height: 16px; width: {percent_width}%; background-color: hsl({hue}, {saturation}%, {lightness}%); border-radius: 4px;"></div>
                        <span style="margin-left: 10px; white-space: nowrap; color: #555; font-size: 14px;">{unique_count:,} ({percentage}%)</span>
                      </div>
                    </div>
                    """

                html += """
                    </div>
                  </div>
                  <div style="display: flex; justify-content: space-between; font-size: 13px; color: #777;">
                    <div>Based on {count} distinct IP addresses</div>
                    <div>{num_countries} countries total</div>
                  </div>
                </div>
                """.format(count=total_unique, num_countries=len(unique_users_df))

                unique_users_html_content = html
            else:
                unique_users_html_content = "<div style='text-align:center; padding: 20px;'>No unique users data available</div>"
        else:
            unique_users_html_content = "<div style='text-align:center; padding: 20px;'>No unique users data available</div>"

        # 4. Model Usage as HTML visualization matching page count style
        model_html = ""
        if 'model_name' in df.columns:
            model_counts = df['model_name'].value_counts().reset_index()
            model_counts.columns = ['model', 'count']

            # Calculate percentages
            total = model_counts['count'].sum()
            model_counts['percentage'] = (model_counts['count'] / total * 100).round(1)

            # Get the maximum count for scaling the bars
            max_count = model_counts['count'].max()

            # Create friendly model names
            model_counts['friendly_name'] = model_counts['model'].apply(
                lambda x: "Standard model" if "Mistral" in x else
                "Advanced model" if "Qwen" in x else x
            )

            # Create HTML for the visualization
            html = """
            <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
              <h3 style="margin-top: 0; margin-bottom: 15px; color: #333;">Model Usage Distribution</h3>
              <div style="display: flex; flex-direction: column; gap: 12px; max-width: 100%;">
            """

            # Create entry for each model
            for _, row in model_counts.iterrows():
                percent_width = min(95, (row['count'] / max_count) * 95) if max_count > 0 else 0

                html += f"""
                <div style="display: flex; align-items: center; width: 100%;">
                  <div style="min-width: 120px; width: 120px; font-weight: 500; color: #444; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{row['model']}">{row['friendly_name']}</div>
                  <div style="flex-grow: 1; display: flex; align-items: center; width: calc(100% - 120px);">
                    <div style="height: 18px; width: {percent_width}%; background-color: #9b59b6; border-radius: 4px;"></div>
                    <span style="margin-left: 10px; white-space: nowrap; color: #555; font-size: 14px;">{row['count']:,} uses ({row['percentage']}%)</span>
                  </div>
                </div>
                """

            html += """
              </div>
              <div style="margin-top: 15px; font-size: 13px; color: #777;">
                Based on {count} total inferences
              </div>
            </div>
            """.format(count=total)

            model_html = html
        else:
            model_html = "<div style='text-align:center; padding: 20px;'>No model usage data available</div>"

        return [
            metrics_html_content,
            duration_html,
            model_html,
            events_plot,
            country_html_content,
            unique_users_html_content
        ]


    # Update dashboard when period changes
    period_selector.change(
        update_dashboard,
        inputs=[period_selector],
        outputs=[
            metrics_html, inference_pages_html, model_usage_html,
            daily_events_plot, country_html, unique_users_html
        ],
        api_name=False  # Explicitly set to None to hide from API
    )

    # Initialize dashboard on load
    demo.load(
        update_dashboard,
        inputs=[gr.State(value="1week")],
        outputs=[
            metrics_html, inference_pages_html, model_usage_html,
            daily_events_plot, country_html, unique_users_html
        ],
        api_name=False  # Explicitly set to None to hide from API
    )

    # Footer with links and version
    with gr.Row(elem_id="footer-container", elem_classes="footer-container"):
        gr.Markdown(
            f"""
            ---
            <p style="text-align: center; margin-top: 8px;">
            Visit <a href="https://katanaml.io/" target="_blank">Katana ML</a> and <a href="https://github.com/katanaml/sparrow" target="_blank">Sparrow</a> GitHub for more details.
            </p>
            <p style="text-align: center; margin-top: 5px;">
            <strong>Version:</strong> {version}
            </p>
            """
        )

# To run this file directly for testing
if __name__ == "__main__":
    # Launch with explicitly disabled API and no documentation
    demo.launch(show_api=False, share=False)