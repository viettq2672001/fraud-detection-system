import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Set

class TransactionAnalyzer:
    def __init__(self, csv_path: str, config: Dict = None):
        """Initialize the transaction analyzer with optional configuration.
        
        Args:
            csv_path: Path to the CSV file containing transaction data
            config: Optional configuration dictionary to override default settings
        """
        # Load and validate data
        if not csv_path or not isinstance(csv_path, str):
            raise ValueError("CSV path must be a non-empty string")
            
        self.df = pd.read_csv(csv_path)
        if self.df.empty:
            raise ValueError("CSV file is empty")
            
        required_columns = {'transaction_id', 'customer_id', 'timestamp', 'amount', 'location', 'merchant_category'}
        if not required_columns.issubset(self.df.columns):
            missing = required_columns - set(self.df.columns)
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert timestamp to datetime
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        # Set up caching
        self._merchant_counts_cache = {}
        
        # Default configurations
        default_config = {
            'high_amount_threshold': 5000.0,
            'rapid_transaction_window_hours': 1,
            'rapid_transaction_count': 3,
            'travel_time_threshold_hours': 2,
            'high_risk_categories': ['Jewelry', 'Electronics'],
            'risk_threshold_percentage': 50.0,
            'enable_caching': True
        }
        
        # Update configuration with provided values
        self.config = default_config
        if config:
            self.config.update(config)
        
        # Initialize thresholds from config
        self.HIGH_AMOUNT_THRESHOLD = self.config['high_amount_threshold']
        self.RAPID_TRANSACTION_WINDOW = timedelta(hours=self.config['rapid_transaction_window_hours'])
        self.RAPID_TRANSACTION_COUNT = self.config['rapid_transaction_count']
        self.TRAVEL_TIME_THRESHOLD = timedelta(hours=self.config['travel_time_threshold_hours'])
        self.HIGH_RISK_CATEGORIES = self.config['high_risk_categories']
        self.RISK_THRESHOLD = self.config['risk_threshold_percentage'] / 100.0
        
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
    
    def _get_merchant_counts(self, customer_id: str, transactions: pd.DataFrame) -> pd.Series:
        """Get cached merchant counts or compute them for a customer.
        
        Args:
            customer_id: The customer ID to get merchant counts for
            transactions: The customer's transactions DataFrame
            
        Returns:
            pd.Series: Count of transactions per merchant category
        """
        if not self.config['enable_caching'] or customer_id not in self._merchant_counts_cache:
            self._merchant_counts_cache[customer_id] = transactions['merchant_category'].value_counts()
        return self._merchant_counts_cache[customer_id]

    def _calculate_risk_score(self, merchant_counts: pd.Series, transactions: pd.DataFrame) -> Dict:
        """Calculate risk score based on both transaction count and amounts.
        
        Args:
            merchant_counts: Count of transactions per merchant category
            transactions: The customer's transactions DataFrame
            
        Returns:
            Dict: Risk calculation results including score and distribution
        """
        total_transactions = len(transactions)
        if total_transactions == 0:
            return None
            
        total_amount = transactions['amount'].sum()
        high_risk_count = 0
        high_risk_amount = 0.0
        
        # Calculate risk based on both transaction count and amount
        for category in self.HIGH_RISK_CATEGORIES:
            if category in merchant_counts:
                cat_transactions = transactions[transactions['merchant_category'] == category]
                cat_count = len(cat_transactions)
                cat_amount = cat_transactions['amount'].sum()
                
                high_risk_count += cat_count
                high_risk_amount += cat_amount
        
        if high_risk_count == 0:
            return None
            
        risk_percentage = (high_risk_count / total_transactions) * 100
        amount_percentage = (high_risk_amount / total_amount) * 100
        
        # Combined risk score weighs both transaction count and amount
        risk_score = (risk_percentage + amount_percentage) / 2
        
        return {
            'total_transactions': total_transactions,
            'high_risk_transactions': high_risk_count,
            'total_amount': total_amount,
            'high_risk_amount': high_risk_amount,
            'merchant_distribution': merchant_counts.to_dict(),
            'risk_percentage': risk_percentage,
            'amount_percentage': amount_percentage,
            'risk_score': risk_score
        }

    def find_unusual_merchant_patterns(self) -> Dict[str, Dict]:
        """Identify customers making unusual patterns of purchases across merchant categories."""
        try:
            unusual_patterns = {}
            
            # Group by customer
            for customer_id, transactions in self.df.groupby('customer_id'):
                # Get merchant categories for this customer
                merchant_counts = self._get_merchant_counts(customer_id, transactions)
                
                # Calculate risk score
                risk_data = self._calculate_risk_score(merchant_counts, transactions)
                if risk_data and risk_data['risk_score'] > self.RISK_THRESHOLD:
                    unusual_patterns[customer_id] = risk_data
            
            return unusual_patterns
            
        except Exception as e:
            print(f"Error in merchant pattern analysis: {str(e)}")
            return {}

    def analyze_transactions(self) -> Dict:
        """Run all fraud detection analyses and return results."""
        return {
            'high_value_transactions': self.find_high_value_transactions().to_dict('records'),
            'rapid_transactions': self.find_rapid_transactions(),
            'impossible_travel': self.find_impossible_travel(),
            'unusual_merchant_patterns': self.find_unusual_merchant_patterns()
        }

def main():
    # Initialize analyzer with sample data and custom configuration
    config = {
        'high_amount_threshold': 5000.0,
        'high_risk_categories': ['Jewelry', 'Electronics'],
        'risk_threshold_percentage': 40.0  # More sensitive detection
    }
    
    try:
        analyzer = TransactionAnalyzer('sample_logs.csv', config)
        
        # Run analysis
        results = analyzer.analyze_transactions()
        
        # Print results
        print("\n=== Fraud Detection Analysis Results ===\n")
        
        print("1. High Value Transactions:")
        for txn in results['high_value_transactions']:
            print(f"Transaction {txn['transaction_id']}: ${txn['amount']:.2f} by {txn['customer_id']} "
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
            print(f"High-risk transactions: {pattern['high_risk_transactions']} "
                  f"(${pattern['high_risk_amount']:.2f})")
            print(f"Transaction Risk: {pattern['risk_percentage']:.1f}%")
            print(f"Amount Risk: {pattern['amount_percentage']:.1f}%")
            print(f"Overall Risk Score: {pattern['risk_score']:.1f}%")
            print("Merchant category distribution:")
            for category, count in pattern['merchant_distribution'].items():
                print(f"  - {category}: {count} transactions")
    
    except Exception as e:
        print(f"Error analyzing transactions: {str(e)}")
