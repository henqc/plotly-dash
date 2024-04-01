#Install all needed dependencies
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

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

@app.callback(
    Output('line-graph', 'figure'),
    [Input('genre-dropdown', 'value'),
     Input('year-slider', 'value')]
)
def update_graph(selected_genres, selected_years):
    if not selected_genres:
        selected_genres = []
    if not selected_years:
        selected_years = [min(years), max(years)]
    
    # Filter the dataframe for the selected years
    filtered_df = df[df['Released_Year'].between(selected_years[0], selected_years[1])]
    
    # Aggregate the genre data over the years, assuming 1 represents a movie in the genre for that year
    genre_data = filtered_df.loc[:, selected_genres + ['Released_Year']]
    genre_popularity = genre_data.groupby('Released_Year')[selected_genres].sum()
    
    # Reset index to make 'Released_Year' a column again for plotting
    genre_popularity = genre_popularity.reset_index()
    
    # Convert dataframe to long format
    df_plottable = pd.melt(genre_popularity, id_vars=['Released_Year'], var_name='Genre', value_name='Popularity')
    
    # Create the line graph
    fig = px.line(df_plottable,
                  x='Released_Year',
                  y='Popularity',
                  color='Genre',
                  line_group='Genre',
                  title='Genre Popularity Over Time',
                  labels={'Popularity': 'Number of Movies', 'Released_Year': 'Year'})
    
    return fig

#App layout to define the structure of the web page
app.layout = html.Div([
    #Contaier div to store all the components
    html.Div(children=[
        #Title describing the purpose of the web app\
        html.H1('Movie Data Visualization Dashboard', style={'textAlign': 'center', 'width': '100%'}), 
        html.Div(children=[
            html.Div(children=[
            dcc.Graph(id='line-graph')  # Graph component where the line graph will be displayed
            ], className='six columns', style={'padding': '0 20px'}),  # Additional padding if needed
            html.Div(children=[
                html.Div(
                    # Movie dropdown component
                    dcc.Dropdown(
                        # Identifier for the movie dropdown component
                        id='movie-dropdown',  
                        #Using the dataframe to populate the options by creating key value pairs with unique movie titles
                        options=[{'label': title, 'value': title} for title in df['Series_Title'].unique()],  
                        #Custom placeholder text to describe what actions to take as a user
                        placeholder = 'Select One or More Movie Title',
                        # Allows user to select multiple movies at once
                        multi=True,  
                    # Styling to fit half the width
                    ), className = 'twelve columns', style={'margin-bottom': '50px', 'margin-top': '100px'}
                ),
                html.Div(
                    # Director dropdown component
                    dcc.Dropdown(
                        # Identifier for the director dropdown component
                        id='director-dropdown',  
                        #Using the dataframe to populate the options by creating key value pairs with unique director names
                        options=[{'label': director, 'value': director} for director in df['Director'].unique()],  
                        #Custom placeholder text to describe what actions to take as a user
                        placeholder = 'Select One or More Director',
                        # Allows user to select multiple directors at once
                        multi=True,  
                    # Styling to fit half the width
                    ), className = 'twelve columns', style={'margin-bottom': '50px'}
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
                    ), className = 'twelve columns', style={'margin-bottom': '50px'}
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
                        marks={str(year): str(year) for year in years[::8]},
                    # Styling to fit half the width
                    ), className = 'twelve columns', style={'margin-bottom': '50px'}
                ),     
            #Styling for the container div that has all components stored in row direction and centers them
            ], className = 'six columns', style={'alignItems': 'flex-end', 'display': 'flex', 'flexDirection': 'column'}),
        #Styling for the container div that has all components stored in row direction and centers them
        ], className='row', style={'display': 'flex', 'alignItems': 'flex-start', 'width': '100%'}),  
    
    #Styling for the container div that has all components stored in column direction and centers them
    ], style={'display': 'flex', 'height': '100vh', 'flex-direction': 'column'}),  
])

#Run the app
if __name__ == '__main__':
    app.run_server(debug=True)