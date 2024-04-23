#Install all needed dependencies
import pandas as pd
import numpy as np 
import plotly.express as px
import plotly.graph_objects as go
from math import floor
from dash import Dash, dcc, html, Input, Output
from dash_iconify import DashIconify

#Read in csv into a pandas data frame
df = pd.read_csv("data.csv")
# load the CSS stylesheet
stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'] 
#Initialize the Dash app
app = Dash(__name__, external_stylesheets=stylesheets)
server = app.server

#sorting years to get the min and max years
years = sorted(int(year) for year in df['Released_Year'].unique())
# Extract genre names from the column headers
genre_columns = df.columns[df.columns.get_loc('Gross')+1:]
# Define a common color palette
common_palette = px.colors.sequential.RdBu

@app.callback(
    Output('line-graph', 'figure'),
    [Input('genre-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('movie-dropdown', 'value')]
)

# Handle the callback to update the stacked area graph
def update_graph(selected_genres, selected_years, selected_movies):
    # Handle selected years range
    if not selected_years:
        selected_years = [min(years), max(years)]
    
    # Filter the dataframe for the selected years
    filtered_df = df[df['Released_Year'].between(selected_years[0], selected_years[1])]

    # Movie selection logic
    if selected_movies:
        movie_genres = df[df['Series_Title'] == (selected_movies)][genre_columns].columns[
            (df[df['Series_Title'] == (selected_movies)][genre_columns] == 1).any()
        ].tolist()
        if not selected_genres:
            selected_genres = movie_genres
        else:
            selected_genres = list(set(selected_genres) | set(movie_genres))
    
    # Default to all genres if none are selected
    if not selected_genres:
        selected_genres = genre_columns.tolist()  

    # Ensure there are genres to process, else return an empty figure
    if selected_genres:
        filtered_df = filtered_df[filtered_df[selected_genres].sum(axis=1) > 0]

        # Group years into bins
        def year_to_bin(year):
            base_year = min(years)
            return f"{int(floor((year - base_year) / 3) * 3 + base_year)}-{int(floor((year - base_year) / 3) * 3 + base_year + 2)}"

        filtered_df['Year_Bin'] = filtered_df['Released_Year'].apply(year_to_bin)
        genre_data = filtered_df.loc[:, selected_genres + ['Year_Bin']]
        genre_popularity = genre_data.groupby('Year_Bin')[selected_genres].sum()
        genre_popularity = genre_popularity.reset_index()
        df_plottable = pd.melt(genre_popularity, id_vars=['Year_Bin'], var_name='Genre', value_name='Popularity')

        # Plot
        fig = px.area(df_plottable,
                      x='Year_Bin',
                      y='Popularity',
                      color='Genre',
                      color_discrete_sequence=common_palette,
                      line_group='Genre',
                      title='Genre Popularity Over Three-Year Bins',
                      labels={'Popularity': 'Number of Movies', 'Year_Bin': 'Year Bin'})
        
        # Add vertical line for selected movie release year
        if selected_movies:
            movie_release_year = df[df['Series_Title'] == (selected_movies)]['Released_Year'].iloc[0] 
            movie_year_bin = year_to_bin(movie_release_year)
            max_popularity = df_plottable[df_plottable['Year_Bin'] == movie_year_bin]['Popularity'].max()
            fig.add_trace(go.Scatter(
                x=[movie_year_bin, movie_year_bin],
                y=[0, max_popularity * 4],
                mode='lines',
                line=dict(color='red', width=2, dash='dash'),
                name='Release Year Bin'
            ))
    else:
        fig = px.area(title='No data to display - select genres and/or movies')
    
    return fig

@app.callback(
    Output('bubble-chart', 'figure'),
    [Input('genre-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('movie-dropdown', 'value')]
)

# Handle the callback to update the bubble graph
def update_bubble_chart(selected_genres, selected_years, selected_movie):
    # Filter dataframe based on selected years
    filtered_df = df[df['Released_Year'].between(selected_years[0], selected_years[1])]
    
    # Filter for selected genres
    if selected_genres:
        filtered_df = filtered_df[filtered_df[selected_genres].sum(axis=1) > 0]
    
    # Aggregate data
    grouped_df = filtered_df.groupby('IMDB_Rating').agg({
        'Gross': 'mean',
        'No_of_Votes': 'mean',
        'Series_Title': 'count'
    }).reset_index().rename(columns={'Series_Title': 'Count_of_Movies'})

    # Average will be red, selected movie will be blue
    grouped_df['label'] = 'Average'  
    grouped_df['color'] = 'red'

    if selected_movie:
        movie_data = df[df['Series_Title'] == selected_movie]
        movie_specific = movie_data[['IMDB_Rating', 'Gross', 'No_of_Votes', 'Series_Title']]
        movie_specific = movie_specific.rename(columns={'Series_Title': 'label'})
        movie_specific['color'] = 'blue'  

        # Concatenate to general grouped DataFrame
        combined_df = pd.concat([grouped_df, movie_specific])
    else:
        combined_df = grouped_df

    color_map = {'Average': '#cb818f', selected_movie: '#92c5de'} if selected_movie else {'Average': '#cb818f'}

    # Plot
    fig = px.scatter(
        combined_df,
        x='IMDB_Rating',
        y='Gross',
        size='No_of_Votes',
        color='label',  
        hover_name='label',  
        title='Average Gross Revenue vs. IMDB Rating',
        color_discrete_map=color_map,
        labels={
            'IMDB_Rating': 'IMDB Rating',
            'Gross': 'Average Gross Revenue ($)',
            'No_of_Votes': 'Average Number of Votes',
            'Count_of_Movies': 'Movies Count',
            'label': 'Category'  
        },
        size_max=60,
        opacity=0.6
    )
    
    return fig

@app.callback(
    Output('ratings-pie-chart', 'figure'),
    [Input('genre-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('movie-dropdown', 'value')]
)

# Handle the callback to update the ratings pie chart
def update_ratings_chart(selected_genres, selected_years, selected_movie):
    if selected_movie:
        # Filter to the selected movie
        filtered_df = df[df['Series_Title'] == selected_movie]
        # If a single movie is selected, display a full pie
        single_movie_df = pd.DataFrame({
            'Rating': [f"{filtered_df['IMDB_Rating'].iloc[0]} Rating"],
            'Count': [1]
        })
        fig = px.pie(single_movie_df, values='Count', names='Rating', title=f"IMDB Rating: {filtered_df['IMDB_Rating'].iloc[0]}", color_discrete_sequence=common_palette,)
    else:
        # Normal genre and year filtering
        filtered_df = df[df['Released_Year'].between(selected_years[0], selected_years[1])]
        if selected_genres:
            filtered_df = filtered_df[filtered_df[selected_genres].sum(axis=1) > 0]
        
        # Define rating bins
        bins = [0, 7.75, 8, 8.25, 8.5, 8.75, 9, 9.25, 9.5] 
        labels = ['<7.75', '7.75-8', '8-8.25', '8.25-8.5', '8.5-8.75', '8.75-9', '9-9.25', '>9.25']
        filtered_df['Rating_Bin'] = pd.cut(filtered_df['IMDB_Rating'], bins=bins, labels=labels, right=False)
        
        # Plot
        fig = px.pie(
            filtered_df,
            names='Rating_Bin',
            title='Distribution of IMDB Ratings',
            color='Rating_Bin',
            color_discrete_sequence=common_palette,
        )

    return fig

@app.callback(
    [Output('movie-dropdown', 'style'), Output('genre-dropdown', 'style'), Output('movie-dropdown', 'value'), Output('genre-dropdown', 'value')],
    [Input('control-radio', 'value')]
)

# Handle the callback to toggle and clear dropdowns
def toggle_and_clear_dropdowns(selected_option):
    if selected_option == 'movie':
        return {'display': 'block'}, {'display': 'none'}, None, None  
    elif selected_option == 'genre':
        return {'display': 'none'}, {'display': 'block'}, None, None  
    return {'display': 'none'}, {'display': 'none'}, None, None  

#App layout to define the structure of the web page
app.layout = html.Div([
    #Title describing the purpose of the web app
    html.H1('Movie Data Visualization Dashboard', className='custom-font', style={'border-radius': '10px', 'padding': '10px', 'background-color' : 'white', 'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'}), 
    #Contaier div to store all the components
    html.Div(children=[
        html.Div(children=[
            html.Div(children=[
                html.H3('Filter Options', className='custom-font', style={}), 
                html.Div(
                    # Control dropdown to select which dropdown to activate
                    dcc.RadioItems(
                    id='control-radio',
                    options=[
                        {'label': 'Select Movie', 'value': 'movie'},
                        {'label': 'Select Genre', 'value': 'genre'}
                    ],
                    value='movie',
                    style={'width': '100%', 'display': 'flex', 'justifyContent': 'center'}
                    ), className='custom-font', style={'margin-bottom': '20px'}
                ),
                html.Div(
                    # Movie dropdown component
                    dcc.Dropdown(
                        # Identifier for the movie dropdown component
                        id='movie-dropdown',  
                        #Using the dataframe to populate the options by creating key value pairs with unique movie titles
                        options=[{'label': title, 'value': title} for title in df['Series_Title'].unique()],  
                        #Custom placeholder text to describe what actions to take as a user
                        placeholder = 'Select One Movie Title',
                    # Styling to fit half the width
                    ), className='custom-font', style={'margin-bottom': '20px', 'textAlign': 'center', 'color': '#888'}
                ),
                html.Div(
                    # Genre dropdown component
                    dcc.Dropdown(
                        # Identifier for the genre dropdown component
                        id='genre-dropdown',  
                        #Using the dataframe to populate the options by creating key value pairs with unique genres
                        options=[{'label': genre, 'value': genre} for genre in genre_columns.unique()],  
                        #Custom placeholder text to describe what actions to take as a user
                        placeholder = 'Select One or More Genre',
                        # Allows user to select multiple genres at once
                        multi=True,  
                    # Styling to fit half the width
                    ), style={'margin-bottom': '20px', 'textAlign': 'center', 'color': '#888'}
                ),
                html.Div(
                    # Year range slider
                    dcc.RangeSlider(
                        # Identifier for the year range slider component
                        id='year-slider',
                        # Lower bound as determined from our sorted year array 
                        min=years[0],
                        # Upper bound as determined from our sorted year array 
                        max=years[-1],
                        # Default to having full range selected
                        value=[years[0], years[-1]],
                        # Put a mark every 10 years for readability
                        marks={str(year): str(year) for year in years[::16]},
                    # Styling to fit half the width
                    ), style={'margin-bottom': '20px'}
                ),     
            ], style = {'border-radius': '10px', 'padding': '10px', 'background-color' : 'white', 'margin-left': '15px', 'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'}),
            # About the dashboard section
            html.Div(children=[
                html.H3('About the Dashboard', style={}), 
                html.Ul(children=[
                    html.Li("Pie chart represents the total distribution of IMDb ratings of individual films within the filtered options"),
                    html.Li("Bubble graph shows how gross revenue is related to IMDb rating"),
                    html.Li("The size of each individual bubble is determined by the number of users who voted on that particular film"),
                    html.Li("The position of the red bubbles are determined by the average gross revenue for films for a given rating"),
                    html.Li("Selecting a movie will display a blue bubble on the bubble graph"),
                    html.Li("Filtering by genre and/or year will filter the bubble graph to only account for movies for the specifications"),
                    html.Li("Stacked area chart represents how popular a genre is for any given time period"),
                    html.Li("Selecting a movie will display only that movies genres on the stacked area chart"),
                    html.Li("Filtering by genre will display those genres on the stacked area chart"),
                    html.Li("Filtering by year will display only the selected time frame on the stacked area chart"),
                ], className='custom-font'),
            ], className='custom-font', style = {'border-radius': '10px', 'padding': '10px', 'background-color' : 'white', 'margin-left': '15px', 'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)', 'margin-top': '20px', 'padding': '15px'}),
        ], className = 'three columns', ),
        # Graphs section
        html.Div(children=[
            html.Div([
                html.Div([
                    dcc.Graph(id='ratings-pie-chart')
                ], className='four columns', style = {'border-radius': '10px', 'padding': '10px', 'background-color' : 'white', 'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'}),

                html.Div([
                    dcc.Graph(id='bubble-chart')
                ], className='eight columns',  style = {'border-radius': '10px', 'padding': '10px', 'background-color' : 'white', 'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'})
            ], className='row', style={'display': 'flex', 'margin-bottom': '20px'}),

            html.Div([
                dcc.Graph(id='line-graph')
            ], className='row', style = {'border-radius': '10px', 'padding': '10px', 'background-color' : 'white', 'box-shadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)'})
        ], className='nine columns', style={'margin-left': '49px','margin-right': '0px'}),  
    ]),  
    # Footer
    html.Footer([
        html.P("Created by Henry Chen"),
        html.Div([
            html.A(
                [
                    DashIconify(
                        icon="devicon:kaggle",
                        width=20,
                        height=20,
                    ),
                ],
                target="_blank",
                href="https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows",
            ),
            html.A(
                [
                    DashIconify(
                        icon="ion:logo-github",
                        width=20,
                        height=20,
                    ),
                ],
                href="https://github.com/henqc/plotly-dash",
                target="_blank",
                className="github",
            ),
        ],
        className="flex", style = {'margin-left': '10px'}
    ),
    ], className='twelve columns custom-font', style={'justify-content': 'center', 'padding': '10px', 'background-color': '#f8f9fa', 'border-top': '1px solid #e9ecef', 'width': '100%', 'margin-top': '20px', 'display': 'flex', 'flex-direction': 'row'}),
])

#Run the app
if __name__ == '__main__':
    app.run(jupyter_mode='tab', debug=True)