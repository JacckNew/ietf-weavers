"""
Main pipeline script that orchestrates graph + NLP + export.
Implements the complete IETF Weavers analysis pipeline.
"""

import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

# Add project root and agent directory to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'agent'))

from agent.graph_builder import SocialGraphBuilder, process_mailing_list_archive
from agent.metrics import NetworkMetrics, calculate_network_metrics
from agent.topic_model import TopicModeler, run_topic_modeling
from agent.formatter import D3Formatter, format_for_visualization
from agent.utils import PersonIdentityResolver, EmailParser
from agent.data_acquisition import IETFDataAcquisition


class IETFWeaversPipeline:
    """
    Main pipeline for IETF Weavers analysis following the methodology:
    
    1. Load emails and metadata
    2. Build graph via graph_builder
    3. Calculate metrics via metrics
    4. Run topic modeling via topic_model
    5. Format and export via formatter
    6. Render in index.html
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.graph_builder = None
        self.metrics_calculator = None
        self.topic_modeler = None
        self.formatter = D3Formatter()
        
        # Results storage
        self.graph = None
        self.metrics_data = None
        self.topic_analysis = None
        self.visualization_data = None
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration for the pipeline."""
        return {
            'data_dir': 'data',
            'output_dir': 'visualisation',
            'n_topics': 50,
            'time_window_months': 6,
            'min_emails_per_person': 5,
            'export_individual_features': True,
            'export_communities': True,
            'export_temporal_snapshots': False
        }
    
    def load_email_data(self, data_source: str) -> List[Dict]:
        """
        Load email data from various sources.
        
        Args:
            data_source: Path to data file or directory
        
        Returns:
            List of email dictionaries
        """
        print(f"Loading email data from: {data_source}")
        
        if not os.path.exists(data_source):
            print(f"Error: Data source {data_source} does not exist")
            return []
        
        # Handle different data formats
        if os.path.isfile(data_source):
            if data_source.endswith('.json'):
                with open(data_source, 'r') as f:
                    return json.load(f)
            elif data_source.endswith('.csv'):
                # TODO: Implement CSV loading
                print("CSV loading not yet implemented")
                return []
            else:
                print(f"Unsupported file format: {data_source}")
                return []
        
        elif os.path.isdir(data_source):
            # Load from directory of files
            email_data = []
            for filename in os.listdir(data_source):
                if filename.endswith('.json'):
                    file_path = os.path.join(data_source, filename)
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            email_data.extend(data)
                        else:
                            email_data.append(data)
            return email_data
        
        return []
    
    def run_phase0_ietf_data_acquisition(self, 
                                        mailing_lists: List[str],
                                        output_file: str = None,
                                        start_date: str = "2023-01-01T00:00:00",
                                        end_date: str = "2024-12-31T23:59:59",
                                        max_messages: Optional[int] = None,
                                        cache_file: str = "ietfdata.sqlite",
                                        use_cache: bool = True) -> List[Dict]:
        """
        Phase 0: IETF Data Acquisition (New)
        - Fetch real IETF mailing list data using glasgow-ipl/ietfdata
        - Fetch IETF Datatracker metadata for person normalization
        - Transform data into pipeline-compatible format
        - Cache data for repeated analysis
        """
        print("=" * 50)
        print("Phase 0: IETF Data Acquisition")
        print("=" * 50)
        
        try:
            # Initialize IETF data acquisition
            data_acq = IETFDataAcquisition(
                cache_file=cache_file,
                use_cache=use_cache,
                log_level="INFO"
            )
            
            # If no specific lists provided, show available lists
            if not mailing_lists:
                print("No mailing lists specified. Available lists:")
                available_lists = data_acq.get_available_mailing_lists()
                for i, mlist in enumerate(available_lists[:20]):  # Show first 20
                    print(f"  {mlist}")
                if len(available_lists) > 20:
                    print(f"  ... and {len(available_lists) - 20} more")
                print("\nSpecify mailing lists with --mailing-lists option")
                return []
            
            # Set default output file if not provided
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.config['data_dir'], f"ietf_data_{timestamp}.json")
            
            # Fetch and save data
            print(f"Fetching data from mailing lists: {', '.join(mailing_lists)}")
            print(f"Date range: {start_date} to {end_date}")
            if max_messages:
                print(f"Max messages: {max_messages}")
            
            success = data_acq.fetch_and_save_data(
                mailing_lists=mailing_lists,
                output_file=output_file,
                start_date=start_date,
                end_date=end_date,
                max_messages=max_messages,
                update_lists=True,  # Update mailing list data
                fetch_person_metadata=True  # Fetch person metadata
            )
            
            if not success:
                print("Failed to fetch IETF data")
                return []
            
            # Load the fetched data for pipeline processing
            print(f"Loading fetched data from: {output_file}")
            with open(output_file, 'r') as f:
                email_data = json.load(f)
            
            print(f"Successfully fetched {len(email_data)} messages from IETF")
            return email_data
        
        except ImportError:
            print("Error: ietfdata library not available")
            print("Install with: pip install ietfdata")
            return []
        
        except Exception as e:
            print(f"Error in IETF data acquisition: {e}")
            return []
    
    def run_phase1_data_collection(self, data_source: str) -> List[Dict]:
        """
        Phase 1: Data Collection & Cleaning
        - Load IETF public mailing list archive
        - Parse headers for sender, date, subject, message ID, and reply reference
        - Normalize identities using Datatracker metadata
        """
        print("=" * 50)
        print("Phase 1: Data Collection & Cleaning")
        print("=" * 50)
        
        # Load raw email data
        email_data = self.load_email_data(data_source)
        print(f"Loaded {len(email_data)} emails")
        
        if not email_data:
            print("No email data loaded. Please check your data source.")
            return []
        
        # Filter out automated emails and apply minimum threshold
        email_parser = EmailParser()
        filtered_emails = []
        
        for email in email_data:
            from_email = email.get('from', '')
            if email_parser.classify_email_type(from_email) == 'individual':
                filtered_emails.append(email)
        
        print(f"Filtered to {len(filtered_emails)} individual emails")
        
        return filtered_emails
    
    def run_phase2_graph_construction(self, email_data: List[Dict]) -> SocialGraphBuilder:
        """
        Phase 2: Social Graph Construction
        - Build directed graph with nodes as participants and edges as reply relationships
        - Compute centrality measures and community detection
        - Track participation duration, area coverage, and mail volume
        """
        print("=" * 50)
        print("Phase 2: Social Graph Construction")
        print("=" * 50)
        
        # Initialize graph builder
        self.graph_builder = SocialGraphBuilder()
        
        # Add emails to graph
        for email in email_data:
            # Extract mailing list from email if available
            mailing_list = email.get('mailing_list', email.get('list_name', ''))
            self.graph_builder.add_email(email, mailing_list)
        
        # Build interaction graph
        print("Building interaction relationships...")
        self.graph_builder.build_interaction_graph()
        self.graph_builder.add_co_participation_edges()
        
        # Get the constructed graph
        self.graph = self.graph_builder.get_graph()
        
        print(f"Graph constructed with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        
        return self.graph_builder
    
    def run_phase3_metrics_calculation(self) -> Dict[str, Any]:
        """
        Phase 3: Network Metrics Calculation
        - Calculate degree, betweenness, closeness centrality
        - Perform community detection using Louvain
        - Compute individual and relationship-level features
        """
        print("=" * 50)
        print("Phase 3: Network Metrics Calculation")
        print("=" * 50)
        
        if not self.graph:
            print("Error: No graph available for metrics calculation")
            return {}
        
        # Calculate network metrics
        self.metrics_calculator = NetworkMetrics(self.graph)
        self.metrics_data = self.metrics_calculator.generate_comprehensive_report()
        
        print(f"Calculated metrics for {len(self.metrics_data.get('individual_features', {}))} individuals")
        print(f"Detected {self.metrics_data.get('community_analysis', {}).get('num_communities', 0)} communities")
        
        return self.metrics_data
    
    def run_phase4_topic_modeling(self, email_data: List[Dict]) -> Dict[str, Any]:
        """
        Phase 4: Topic Modeling (BERTopic)
        - Concatenate each user's emails into documents per time window
        - Extract 50-100 topics and participant-topic distributions
        - Calculate topic entropy for each participant
        """
        print("=" * 50)
        print("Phase 4: Topic Modeling")
        print("=" * 50)
        
        if not self.graph_builder:
            print("Error: No graph builder available for topic modeling")
            return {}
        
        # Run topic modeling
        person_resolver = self.graph_builder.get_person_resolver()
        self.topic_modeler = run_topic_modeling(
            email_data, 
            person_resolver,
            n_topics=self.config['n_topics'],
            time_window_months=self.config['time_window_months']
        )
        
        # Export topic analysis
        if self.topic_modeler.model:
            output_file = os.path.join(self.config['output_dir'], 'topic_analysis.json')
            self.topic_analysis = self.topic_modeler.export_topic_analysis(output_file, person_resolver)
            print(f"Topic analysis exported to {output_file}")
        else:
            print("Topic modeling failed or dependencies not available")
            self.topic_analysis = {}
        
        return self.topic_analysis
    
    def run_phase5_formatting_export(self) -> Dict[str, Any]:
        """
        Phase 4: Output for Visualisation
        - Format graph and topic data for D3.js
        - Export as visualisation/data.json
        """
        print("=" * 50)
        print("Phase 5: Formatting and Export")
        print("=" * 50)
        
        if not self.graph or not self.metrics_data:
            print("Error: Missing graph or metrics data for formatting")
            return {}
        
        # Get community assignments
        communities = self.metrics_data.get('community_analysis', {}).get('communities', {})
        
        # Format for visualization
        person_resolver = self.graph_builder.get_person_resolver()
        self.visualization_data = format_for_visualization(
            self.graph,
            self.metrics_data,
            person_resolver,
            self.topic_analysis,
            communities
        )
        
        # Export main visualization data
        output_file = os.path.join(self.config['output_dir'], 'data.json')
        self.formatter.export_d3_json(
            output_file,
            self.visualization_data,
            self.topic_analysis.get('topics', []) if self.topic_analysis else [],
            self.visualization_data.get('metadata', {})
        )
        
        print(f"Visualization data exported to {output_file}")
        
        # Export additional data files if requested
        if self.config.get('export_individual_features'):
            features_file = os.path.join(self.config['output_dir'], 'individual_features.csv')
            if hasattr(self.metrics_calculator, 'export_features_csv'):
                try:
                    self.metrics_calculator.export_features_csv(features_file)
                    print(f"Individual features exported to {features_file}")
                except Exception as e:
                    print(f"Warning: Could not export individual features: {e}")
        
        # Export person mappings
        if person_resolver:
            person_resolver.export_mappings(self.config['data_dir'])
            print("Person identity mappings exported")
        
        return self.visualization_data
    
    def run_complete_pipeline(self, data_source: str) -> Dict[str, Any]:
        """
        Run the complete IETF Weavers analysis pipeline.
        
        Args:
            data_source: Path to email data
        
        Returns:
            Complete analysis results
        """
        print("🧠 IETF Weavers Analysis Pipeline")
        print("=" * 50)
        print(f"Data source: {data_source}")
        print(f"Configuration: {self.config}")
        print("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # Phase 1: Data Collection & Cleaning
            email_data = self.run_phase1_data_collection(data_source)
            if not email_data:
                return {}
            
            # Phase 2: Social Graph Construction
            self.run_phase2_graph_construction(email_data)
            if not self.graph:
                return {}
            
            # Phase 3: Network Metrics Calculation
            self.run_phase3_metrics_calculation()
            
            # Phase 4: Topic Modeling
            self.run_phase4_topic_modeling(email_data)
            
            # Phase 5: Formatting and Export
            self.run_phase5_formatting_export()
            
            # Summary
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("=" * 50)
            print("✅ Pipeline completed successfully!")
            print(f"⏱️  Total duration: {duration}")
            print(f"📊 Network: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            if self.topic_analysis:
                print(f"🏷️  Topics: {len(self.topic_analysis.get('topics', []))}")
            print(f"📁 Output: {self.config['output_dir']}/data.json")
            print("=" * 50)
            
            return {
                'success': True,
                'duration': str(duration),
                'graph': self.graph,
                'metrics': self.metrics_data,
                'topics': self.topic_analysis,
                'visualization': self.visualization_data
            }
            
        except Exception as e:
            print(f"❌ Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='IETF Weavers Analysis Pipeline')
    parser.add_argument('data_source', nargs='?', help='Path to email data file or directory (optional if using --fetch-ietf)')
    parser.add_argument('--output-dir', default='visualisation', help='Output directory')
    parser.add_argument('--n-topics', type=int, default=50, help='Number of topics for modeling')
    parser.add_argument('--time-window', type=int, default=6, help='Time window in months')
    
    # IETF data acquisition options
    parser.add_argument('--fetch-ietf', action='store_true', 
                        help='Fetch data from IETF using ietfdata library')
    parser.add_argument('--mailing-lists', nargs='+',
                        help='IETF mailing lists to fetch (e.g., ietf cfrg)')
    parser.add_argument('--start-date', default='2023-01-01T00:00:00',
                        help='Start date for IETF data (ISO format)')
    parser.add_argument('--end-date', default='2024-12-31T23:59:59',
                        help='End date for IETF data (ISO format)')
    parser.add_argument('--max-messages', type=int,
                        help='Maximum messages to fetch from IETF')
    parser.add_argument('--cache-file', default='ietfdata.sqlite',
                        help='SQLite cache file for ietfdata')
    parser.add_argument('--no-cache', action='store_true',
                        help='Use live queries instead of cache')
    parser.add_argument('--list-available', action='store_true',
                        help='List available IETF mailing lists and exit')
    
    args = parser.parse_args()
    
    # Handle list available mailing lists
    if args.list_available:
        try:
            from agent.data_acquisition import IETFDataAcquisition
            data_acq = IETFDataAcquisition(
                cache_file=args.cache_file,
                use_cache=not args.no_cache
            )
            print("Available IETF mailing lists:")
            lists = data_acq.get_available_mailing_lists()
            for mlist in lists[:50]:  # Show first 50
                print(f"  {mlist}")
            if len(lists) > 50:
                print(f"  ... and {len(lists) - 50} more")
            return 0
        except Exception as e:
            print(f"Error listing mailing lists: {e}")
            return 1
    
    # Validate arguments
    if not args.fetch_ietf and not args.data_source:
        parser.error("Either provide data_source or use --fetch-ietf")
    
    # Configuration
    config = {
        'data_dir': 'data',
        'output_dir': args.output_dir,
        'n_topics': args.n_topics,
        'time_window_months': args.time_window,
        'min_emails_per_person': 5,
        'export_individual_features': True,
        'export_communities': True
    }
    
    # Create output directory
    os.makedirs(config['output_dir'], exist_ok=True)
    os.makedirs(config['data_dir'], exist_ok=True)
    
    # Run pipeline
    pipeline = IETFWeaversPipeline(config)
    
    # Determine data source
    if args.fetch_ietf:
        # Fetch IETF data first
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ietf_data_file = os.path.join(config['data_dir'], f"ietf_data_{timestamp}.json")
        
        email_data = pipeline.run_phase0_ietf_data_acquisition(
            mailing_lists=args.mailing_lists or [],
            output_file=ietf_data_file,
            start_date=args.start_date,
            end_date=args.end_date,
            max_messages=args.max_messages,
            cache_file=args.cache_file,
            use_cache=not args.no_cache
        )
        
        if not email_data:
            print("Failed to fetch IETF data")
            return 1
        
        # Use the fetched data as data source
        data_source = ietf_data_file
    else:
        data_source = args.data_source
    
    # Run the rest of the pipeline
    results = pipeline.run_complete_pipeline(data_source)
    
    if results.get('success'):
        print("\n🎉 Ready for visualization! Open visualisation/index.html to view results.")
    else:
        print(f"\n❌ Pipeline failed: {results.get('error', 'Unknown error')}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())