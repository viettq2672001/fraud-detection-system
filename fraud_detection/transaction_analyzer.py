import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Set

class TransactionAnalyzer:
    def __init__(self, csv_path: str):
        self.df = pd.read_csv(csv_path)
        # Convert timestamp to datetime
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # Thresholds
        self.HIGH_AMOUNT_THRESHOLD = 5000.0  # Transactions above this amount are suspicious
        self.RAPID_TRANSACTION_WINDOW = timedelta(hours=1)  # Time window for rapid transactions
        self.RAPID_TRANSACTION_COUNT = 3  # Number of transactions within window to be suspicious
        self.TRAVEL_TIME_THRESHOLD = timedelta(hours=2)  # Minimum time expected between different locations
        
    def find_high_value_transactions(self) -> pd.DataFrame:
        """Identify transactions above the high amount threshold."""
        return self.df[self.df['amount'] > self.HIGH_AMOUNT_THRESHOLD]
    
    def find_rapid_transactions(self) -> Dict[str, List[Dict]]:
        """Identify customers making many transactions in a short time period."""
        suspicious_patterns = {}
        
        # Group by customer
        for customer_id, transactions in self.df.groupby('customer_id'):
            # Sort transactions by timestamp
            sorted_txns = transactions.sort_values('timestamp')
            
            # Check each transaction window
            for i in range(len(sorted_txns) - self.RAPID_TRANSACTION_COUNT + 1):
                window = sorted_txns.iloc[i:i + self.RAPID_TRANSACTION_COUNT]
                time_diff = window.iloc[-1]['timestamp'] - window.iloc[0]['timestamp']
                
                if time_diff <= self.RAPID_TRANSACTION_WINDOW:
                    if customer_id not in suspicious_patterns:
                        suspicious_patterns[customer_id] = []
                    
                    suspicious_patterns[customer_id].append({
                        'transactions': window['transaction_id'].tolist(),
                        'time_window': time_diff,
                        'total_amount': window['amount'].sum()
                    })
        
        return suspicious_patterns
    
    def find_impossible_travel(self) -> List[Dict]:
        """Identify transactions in different locations with impossible travel times."""
        suspicious_travel = []
        
        # Group by customer
        for customer_id, transactions in self.df.groupby('customer_id'):
            # Sort transactions by timestamp
            sorted_txns = transactions.sort_values('timestamp')
            
            # Compare consecutive transactions
            for i in range(len(sorted_txns) - 1):
                curr_txn = sorted_txns.iloc[i]
                next_txn = sorted_txns.iloc[i + 1]
                
                if curr_txn['location'] != next_txn['location']:
                    time_diff = next_txn['timestamp'] - curr_txn['timestamp']
                    
                    if time_diff < self.TRAVEL_TIME_THRESHOLD:
                        suspicious_travel.append({
                            'customer_id': customer_id,
                            'transaction1': {
                                'id': curr_txn['transaction_id'],
                                'location': curr_txn['location'],
                                'timestamp': curr_txn['timestamp']
                            },
                            'transaction2': {
                                'id': next_txn['transaction_id'],
                                'location': next_txn['location'],
                                'timestamp': next_txn['timestamp']
                            },
                            'time_difference': time_diff
                        })
        
        return suspicious_travel
    
    def find_unusual_merchant_patterns(self) -> Dict[str, List[Dict]]:
        """Identify customers making unusual patterns of purchases across merchant categories."""
        unusual_patterns = {}
        
        # Group by customer
        for customer_id, transactions in self.df.groupby('customer_id'):
            # Get merchant categories for this customer
            merchant_counts = transactions['merchant_category'].value_counts()
            total_transactions = len(transactions)
            
            # Look for customers who make more than 50% of their transactions in high-risk categories
            high_risk_categories = ['Jewelry', 'Electronics']
            high_risk_count = sum(merchant_counts[cat] for cat in high_risk_categories 
                                if cat in merchant_counts)
            
            if high_risk_count / total_transactions > 0.5:
                unusual_patterns[customer_id] = {
                    'total_transactions': total_transactions,
                    'high_risk_transactions': high_risk_count,
                    'merchant_distribution': merchant_counts.to_dict(),
                    'risk_percentage': (high_risk_count / total_transactions) * 100
                }
        
        return unusual_patterns

    def analyze_transactions(self) -> Dict:
        """Run all fraud detection analyses and return results."""
        return {
            'high_value_transactions': self.find_high_value_transactions().to_dict('records'),
            'rapid_transactions': self.find_rapid_transactions(),
            'impossible_travel': self.find_impossible_travel(),
            'unusual_merchant_patterns': self.find_unusual_merchant_patterns()
        }

def main():
    # Initialize analyzer with sample data
    analyzer = TransactionAnalyzer('sample_logs.csv')
    
    # Run analysis
    results = analyzer.analyze_transactions()
    
    # Print results
    print("\n=== Fraud Detection Analysis Results ===\n")
    
    print("1. High Value Transactions:")
    for txn in results['high_value_transactions']:
        print(f"Transaction {txn['transaction_id']}: ${txn['amount']} by {txn['customer_id']} "
              f"in {txn['location']} at {txn['timestamp']}")
    
    print("\n2. Rapid Transactions:")
    for customer_id, patterns in results['rapid_transactions'].items():
        print(f"\nCustomer {customer_id}:")
        for pattern in patterns:
            print(f"Made {len(pattern['transactions'])} transactions in "
                  f"{pattern['time_window'].total_seconds()/60:.1f} minutes")
            print(f"Transaction IDs: {', '.join(pattern['transactions'])}")
            print(f"Total amount: ${pattern['total_amount']:.2f}")
    
    print("\n3. Impossible Travel Patterns:")
    for travel in results['impossible_travel']:
        print(f"\nCustomer {travel['customer_id']}:")
        print(f"Transaction {travel['transaction1']['id']} in {travel['transaction1']['location']}")
        print(f"Transaction {travel['transaction2']['id']} in {travel['transaction2']['location']}")
        print(f"Time difference: {travel['time_difference'].total_seconds()/60:.1f} minutes")
    
    print("\n4. Unusual Merchant Patterns:")
    for customer_id, pattern in results['unusual_merchant_patterns'].items():
        print(f"\nCustomer {customer_id}:")
        print(f"Total transactions: {pattern['total_transactions']}")
        print(f"High-risk transactions: {pattern['high_risk_transactions']}")
        print(f"Risk percentage: {pattern['risk_percentage']:.1f}%")
        print("Merchant category distribution:")
        for category, count in pattern['merchant_distribution'].items():
            print(f"  - {category}: {count} transactions")

if __name__ == "__main__":
    main()
