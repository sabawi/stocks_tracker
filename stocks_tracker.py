"""
Author: Al Sabawi
Date: July 2024
Purpose: This script tracks stock prices, calculates changes, and displays the information in a terminal interface using the curses library.

It fetches stock data using the yfinance library, calculates price changes, and displays the results in a table format. 
The table updates every `interval` seconds and can be exited by pressing 'q'.
"""

import sys  # Import the sys module for command-line arguments and system exit
import time  # Import the time module for sleeping between updates
import curses  # Import the curses module for terminal-based user interfaces
import yfinance as yf  # Import yfinance for fetching stock market data
import pandas as pd  # Import pandas for data manipulation and analysis
from datetime import time as dt_time  # Import the time class for handling specific time comparisons
from prettytable import PrettyTable  # Import PrettyTable for creating formatted tables

def get_stock_data(symbol):
    """
    Fetch historical stock data for a given symbol.

    Args:
        symbol (str): The stock symbol for which to fetch data.
    
    Returns:
        tuple: Contains two DataFrames - historical stock data for the past month and minute-by-minute data for the last day.
    """
    try:
        # Fetch historical data for the past month with daily intervals
        stock_hist = yf.Ticker(symbol).history(period="1mo", interval='1d')
        # Fetch minute-by-minute data for the last day
        lastday_hist = yf.Ticker(symbol).history(period='1d', interval='1m')
        return stock_hist, lastday_hist
    except IndexError:
        # Handle errors by printing an error message and exiting the program
        print(f"Error while getting data for '{symbol}'")
        sys.exit()

def calculate_price_changes(stock_hist, lastday_hist):
    """
    Calculate price changes and determine if the data is intra-day or end-of-day.

    Args:
        stock_hist (DataFrame): Historical daily stock data.
        lastday_hist (DataFrame): Minute-by-minute stock data for the last day.
    
    Returns:
        tuple: Contains last price, previous close price, price change, percentage change, session type, and last close date.
    """
    lastprice = round(stock_hist.iloc[-1].Close, 2)  # Get the last closing price for the month
    yesterday_close = round(stock_hist.iloc[-2].Close, 2)  # Get the previous day's close price
    last_close = round(lastday_hist.iloc[-1].Close, 2)  # Get the last closing price for the day
    last_close_date = lastday_hist.index[-1]  # Get the last date from the minute data
    four_pm = dt_time(15, 59, 0)  # Define the time for comparison to determine session type

    # Check if the last data point is before 4 PM
    if lastday_hist.index[-1].time() < four_pm:
        lastprice = last_close  # Update the last price to the minute-by-minute close price
        intra_day = "INTRADAY"  # Mark as intra-day data
    else:
        intra_day = "EOD"  # Mark as end-of-day data
    
    # Calculate price change and percentage change
    price_change = round(lastprice - yesterday_close, 2)
    change_percent = round(100 * price_change / yesterday_close, 2)
    return lastprice, yesterday_close, price_change, change_percent, intra_day, last_close_date

def format_prettytable(df):
    """
    Format a DataFrame into a PrettyTable object for display.

    Args:
        df (DataFrame): Data to be formatted into a table.
    
    Returns:
        PrettyTable: A PrettyTable object with formatted table data.
    """
    table = PrettyTable()  # Create a PrettyTable object
    table.field_names = df.columns.tolist()  # Set the table's column headers based on DataFrame columns

    for index, row in df.iterrows():  # Iterate over DataFrame rows
        formatted_row = []
        for col, value in row.items():  # Iterate over DataFrame columns
            formatted_row.append(value)  # Append each cell's value to the row
        table.add_row(formatted_row)  # Add the row to the table

    return table  # Return the formatted table

def main(stdscr, stocks, interval):
    """
    Main function to run the curses-based terminal UI for stock tracking.

    Args:
        stdscr (curses window): The standard curses window object.
        stocks (list): List of stock symbols to track.
        interval (int): Time in seconds between updates.
    """
    curses.curs_set(0)  # Hide the cursor
    stdscr.nodelay(1)  # Set the window to non-blocking mode for user input
    stdscr.timeout(1000)  # Set a 1-second timeout for checking user input

    # Initialize color pairs for the table display
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green for positive changes
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)  # Red for negative changes
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)  # White for neutral or default text

    while True:
        results = []
        for symbol in stocks:
            # Loop until data is successfully fetched or max 3 attempts
            looped = 0
            while looped < 3:
                stock_hist, lastday_hist = get_stock_data(symbol)  # Fetch stock data
                if (len(stock_hist) < 2):
                    time.sleep(10)  # Wait for 10 seconds before retrying
                    looped += 1  # Increment retry counter
                    continue
                else:
                    break  # Break the loop if data is successfully fetched
            if(len(stock_hist) < 2):
                print(f"Error while getting data for '{symbol}'")  # Print an error message if data is still insufficient
                return  # Exit the program if data fetching fails

            # Calculate price changes and other relevant information
            lastprice, yesterday_close, price_change, change_percent, intra_day, last_close_date = calculate_price_changes(stock_hist, lastday_hist)
            results.append({
                "Date/Time": last_close_date.strftime('%I:%M%p %m,%d,%y'),  # Format the date and time
                "Symbol": symbol.upper(),  # Convert symbol to uppercase
                "Last Price": lastprice,  # Last price of the stock
                "Prev. Close": yesterday_close,  # Previous day's closing price
                "Change ($)": price_change,  # Change in price
                "Change (%)": change_percent,  # Percentage change in price
                "Session": intra_day  # Session type (INTRADAY or EOD)
            })

        df = pd.DataFrame(results)  # Convert results list to a DataFrame
        df = df.sort_values("Change (%)", ascending=False)  # Sort DataFrame by percentage change in descending order
        formatted_table = format_prettytable(df)  # Format DataFrame into a PrettyTable object

        stdscr.clear()  # Clear the screen
        height, width = stdscr.getmaxyx()  # Get the height and width of the terminal
        table_str = str(formatted_table)  # Convert PrettyTable object to string
        
        lines = table_str.split('\n')  # Split table string into lines
        for i, line in enumerate(lines):  # Iterate over lines of the table
            if i >= height - 1:
                break  # Stop if we reach the bottom of the screen
            if i == 0 or i == 1 or i == len(lines) - 1:
                stdscr.addstr(i, 0, line[:width - 1], curses.color_pair(3) | curses.A_BOLD)  # Print header and footer lines
            else:
                parts = line.split('|')  # Split line into columns
                for j, part in enumerate(parts):  # Iterate over columns
                    if j == 5 or j == 6:  # Highlight "Change ($)" and "Change (%)" columns
                        try:
                            value = float(part.strip())  # Convert part to float for comparison
                            if value > 0:
                                stdscr.addstr(i, line.index(part), part.strip(), curses.color_pair(1) | curses.A_BOLD)  # Green for positive change
                            elif value < 0:
                                stdscr.addstr(i, line.index(part), part.strip(), curses.color_pair(2) | curses.A_BOLD)  # Red for negative change
                            else:
                                stdscr.addstr(i, line.index(part), part.strip(), curses.color_pair(3) | curses.A_BOLD)  # White for no change
                        except ValueError:
                            stdscr.addstr(i, line.index(part), part.strip(), curses.color_pair(3) | curses.A_BOLD)  # Default color for non-numeric columns
                    else:
                        stdscr.addstr(i, line.index(part), part.strip(), curses.color_pair(3) | curses.A_BOLD)  # Default color for other columns
        
        stdscr.refresh()  # Refresh the screen to display the updated table

        if stdscr.getch() == ord('q'):
            break  # Exit the loop if 'q' is pressed

        time.sleep(interval)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stocks_tracker.py <stocks_file> [interval]")
        sys.exit(1)

    stocks_file = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    with open(stocks_file, 'r') as f:
        stocks = f.read().strip().split()

    curses.wrapper(main, stocks, interval)
