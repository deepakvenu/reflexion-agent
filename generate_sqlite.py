import sqlite3
import random
import string

# Function to generate a random M_ID
def generate_m_id():
    return f"MOLY{''.join(random.choices(string.digits, k=8))}"

# Function to generate a realistic problem description
def generate_problem_description():
    descriptions = [
        "Unexpected disconnect from the wireless network.",
        "High latency observed during peak hours.",
        "Failed handover between two access points.",
        "Packet loss detected during data transfer.",
        "Authentication issues with the wireless network.",
        "Intermittent connection drops in the living room.",
        "Weak signal in a multi-floor building.",
        "Device unable to join the network intermittently.",
        "Wi-Fi calling not functioning as expected.",
        "Slow internet speed when multiple devices are connected."
    ]
    return random.choice(descriptions)

# Function to generate a realistic title
def generate_title():
    titles = [
        "Wireless Disconnect Issue",
        "Latency Spike Observed",
        "Access Point Handover Failure",
        "Data Transfer Packet Loss",
        "Authentication Failure",
        "Intermittent Connection Drops",
        "Signal Strength Weakness",
        "Network Join Failure",
        "Wi-Fi Calling Issue",
        "Slow Internet Speed"
    ]
    return random.choice(titles)

# Function to generate realistic repeat steps
def generate_repeat_steps():
    steps = [
        "Connect to the wireless network and monitor the signal strength.",
        "Run a speed test during peak hours to observe latency.",
        "Move between two access points to replicate handover issues.",
        "Start a file transfer and observe the packet loss in the log.",
        "Try connecting with different authentication methods.",
        "Observe connection stability over a period of 1 hour.",
        "Test the connection in areas with weak signal strength.",
        "Attempt to join the network with different devices.",
        "Place a Wi-Fi call and monitor its performance.",
        "Connect multiple devices and check the speed degradation."
    ]
    repeat_step = random.choice(steps)
    # Optionally add a log URL and log file name
    if random.random() > 0.5:  # 50% chance to include log details
        repeat_step += f" Log URL: http://logserver.com/log{random.randint(1000,9999)} Log File: log_{random.randint(1000,9999)}.txt"
    return repeat_step

if __name__ == "__main__":
    # Create the SQLite database in a file
    db_path = './db_path/issues_database.sqlite'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issues (
        M_ID TEXT PRIMARY KEY,
        Description TEXT,
        Title TEXT,
        Repeat_Steps TEXT
    )
    """)

    # Insert 100 dummy entries
    for _ in range(100):
        m_id = generate_m_id()
        description = generate_problem_description()
        title = generate_title()
        repeat_steps = generate_repeat_steps()
        
        cursor.execute("""
        INSERT INTO issues (M_ID, Description, Title, Repeat_Steps) 
        VALUES (?, ?, ?, ?)
        """, (m_id, description, title, repeat_steps))

    # Commit changes and close the connection
    conn.commit()
    conn.close()



