#!/usr/bin/env python3
"""
Diagnostic script to check prediction data structure and forecast format
Run from backend directory: python check_prediction_format.py
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models import Prediction, TrainingRound
from app.services.prediction_service import PredictionService


def check_prediction_format():
    """Check if predictions have proper forecast_data structure"""
    
    db = SessionLocal()
    
    try:
        # Get recent predictions
        predictions = db.query(Prediction).order_by(Prediction.id.desc()).limit(5).all()
        
        if not predictions:
            print("❌ No predictions found in database")
            return
        
        print("=" * 80)
        print("PREDICTION FORMAT DIAGNOSTIC")
        print("=" * 80)
        
        for pred in predictions:
            print(f"\n📋 Prediction #{pred.id}")
            print(f"   Target: {pred.target_column}")
            print(f"   Horizon: {pred.forecast_horizon}h")
            print(f"   Hospital: {pred.hospital_name}")
            
            #Get full detail
            try:
                detail = PredictionService.get_prediction_detail(pred.id, db)
                
                if not detail:
                    print("   ❌ Could not get prediction detail")
                    continue
                
                # Check forecast_data
                forecast_data = detail.get('forecast_data', {})
                
                if not forecast_data:
                    print("   ⚠️  forecast_data is empty")
                    continue
                
                print(f"   📊 forecast_data keys: {list(forecast_data.keys())}")
                
                # Check each format
                if 'forecasts' in forecast_data:
                    forecasts = forecast_data['forecasts']
                    if isinstance(forecasts, list):
                        print(f"   ✓ forecasts: list of {len(forecasts)} items")
                        if forecasts:
                            print(f"     Sample: {json.dumps(forecasts[0], indent=8)}")
                    else:
                        print(f"   ⚠️  forecasts: not a list ({type(forecasts).__name__})")
                
                if 'horizon_forecasts' in forecast_data:
                    hf = forecast_data['horizon_forecasts']
                    if isinstance(hf, dict):
                        print(f"   ✓ horizon_forecasts: dict with keys {list(hf.keys())}")
                        first_key = next(iter(hf.keys())) if hf else None
                        if first_key:
                            print(f"     Sample '{first_key}': {json.dumps(hf[first_key], indent=8)}")
                    else:
                        print(f"   ⚠️  horizon_forecasts: not a dict ({type(hf).__name__})")
                
                if 'horizons' in forecast_data:
                    horizons = forecast_data['horizons']
                    if isinstance(horizons, dict):
                        print(f"   ✓ horizons: dict with keys {list(horizons.keys())}")
                        first_key = next(iter(horizons.keys())) if horizons else None
                        if first_key:
                            print(f"     Sample '{first_key}': {json.dumps(horizons[first_key], indent=8)}")
                    else:
                        print(f"   ⚠️  horizons: not a dict ({type(horizons).__name__})")
                
                # Check metrics
                if 'quality_metrics' in forecast_data:
                    print(f"   ✓ quality_metrics: {forecast_data['quality_metrics']}")
                
                if 'regression_metrics' in forecast_data:
                    print(f"   ✓ regression_metrics: {forecast_data['regression_metrics']}")
                
                # Check AI summary
                if 'ai_summary' in forecast_data:
                    ai_summary = forecast_data['ai_summary']
                    if ai_summary and len(ai_summary) > 20:
                        print(f"   ✓ ai_summary: {len(ai_summary)} chars")
                        print(f"     Preview: {ai_summary[:100]}...")
                    else:
                        print(f"   ⚠️  ai_summary: {len(ai_summary) if ai_summary else 0} chars (too short)")
                
            except Exception as e:
                print(f"   ❌ Error getting detail: {str(e)}")
        
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print("""
If all predictions show:
✓ forecasts, horizon_forecasts, or horizons (with actual data)
✓ quality_metrics or regression_metrics
✓ ai_summary (> 20 chars)

Then the frontend should render charts properly!

If you see ⚠️ or ❌ markers, the issue is backend data structure.
""")
        
    finally:
        db.close()


def validate_forecast_parsing():
    """Test the forecast parsing logic from frontend"""
    
    print("\n" + "=" * 80)
    print("FORECAST PARSING VALIDATION")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        predictions = db.query(Prediction).order_by(Prediction.id.desc()).limit(3).all()
        
        for pred in predictions:
            print(f"\n🔍 Testing Prediction #{pred.id}")
            
            try:
                detail = PredictionService.get_prediction_detail(pred.id, db)
                forecast_data = detail.get('forecast_data', {})
                
                # Simulate frontend parsing
                visualization_forecasts = []
                
                # Format 1: Direct forecasts array
                if isinstance(forecast_data.get('forecasts'), list) and forecast_data['forecasts']:
                    visualization_forecasts = forecast_data['forecasts']
                    print(f"   ✓ Using 'forecasts' format: {len(visualization_forecasts)} items")
                
                # Format 2: horizon_forecasts dict
                elif isinstance(forecast_data.get('horizon_forecasts'), dict) and forecast_data['horizon_forecasts']:
                    entries = forecast_data['horizon_forecasts']
                    visualization_forecasts = [
                        {
                            'hour_ahead': int(str(k).replace('h', '') or '0'),
                            'prediction': v.get('prediction'),
                            'lower_bound': v.get('lower_bound'),
                            'upper_bound': v.get('upper_bound'),
                        }
                        for k, v in entries.items()
                    ]
                    print(f"   ✓ Using 'horizon_forecasts' format: {len(visualization_forecasts)} items")
                
                # Format 3: horizons dict (TFT)
                elif isinstance(forecast_data.get('horizons'), dict) and forecast_data['horizons']:
                    entries = forecast_data['horizons']
                    visualization_forecasts = [
                        {
                            'hour_ahead': int(str(k).replace('h', '') or '0'),
                            'prediction': v.get('p50'),
                            'lower_bound': v.get('p10'),
                            'upper_bound': v.get('p90'),
                        }
                        for k, v in entries.items()
                    ]
                    print(f"   ✓ Using 'horizons' format (TFT): {len(visualization_forecasts)} items")
                
                else:
                    print(f"   ❌ No recognized forecast format found!")
                    continue
                
                # Filter valid entries
                clean_forecasts = [
                    item for item in visualization_forecasts
                    if (isinstance(item.get('hour_ahead'), (int, float)) and 
                        isinstance(item.get('prediction'), (int, float)))
                ]
                
                print(f"   After filtering: {len(clean_forecasts)} valid entries")
                
                if clean_forecasts:
                    print(f"   ✓ CHARTS WILL RENDER")
                    # Show samples
                    for item in clean_forecasts[:2]:
                        print(f"     Sample: hour_ahead={item['hour_ahead']}, prediction={item['prediction']}")
                else:
                    print(f"   ❌ NO VALID FORECASTS - Charts won't render")
                    if visualization_forecasts:
                        print(f"   Debug info (first item):")
                        print(f"   {json.dumps(visualization_forecasts[0], indent=6)}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    finally:
        db.close()


if __name__ == '__main__':
    check_prediction_format()
    validate_forecast_parsing()
