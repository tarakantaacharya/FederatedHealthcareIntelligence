"""
PDF Report Generation Service

Generates comprehensive prediction reports with:
- AI-powered summaries
- Visualization charts (forecast, confidence intervals, metrics)
- Professional formatting for healthcare stakeholders
"""
import io
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus import Frame, PageTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

from app.services.gemini_service import GeminiService


class ReportGenerationService:
    """Generate comprehensive PDF reports for predictions"""

    @staticmethod
    def generate_prediction_report(
        prediction_record: Dict[str, Any],
        hospital_info: Dict[str, Any],
        output_path: str = None
    ) -> bytes:
        """
        Generate comprehensive PDF report for a prediction

        Args:
            prediction_record: Full prediction record from database
            hospital_info: Hospital details
            output_path: Optional file path to save PDF

        Returns:
            PDF bytes
        """
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=20
        )
        body_style = styles['BodyText']
        body_style.fontSize = 11
        body_style.leading = 14

        # Build document content
        story = []

        # Title
        story.append(Paragraph("Prediction Report", title_style))
        story.append(Paragraph(f"<b>Hospital:</b> {hospital_info.get('hospital_name', 'N/A')}", body_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
        story.append(Spacer(1, 0.3*inch))

        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        # Get AI insights
        insights = GeminiService.generate_report_insights(prediction_record)
        
        executive_summary = insights.get('executive_summary', 'No summary available.')
        story.append(Paragraph(executive_summary, body_style))
        story.append(Spacer(1, 0.2*inch))

        # Prediction Details
        story.append(Paragraph("Prediction Details", heading_style))
        
        details_data = [
            ['Target Variable', prediction_record.get('target_column', 'N/A')],
            ['Model Type', prediction_record.get('model_type', 'N/A')],
            ['Forecast Horizon', f"{prediction_record.get('forecast_horizon', 'N/A')} hours"],
            ['Prediction Timestamp', str(prediction_record.get('prediction_timestamp', 'N/A'))],
            ['Round Number', str(prediction_record.get('round_number', 'N/A'))],
        ]
        
        details_table = Table(details_data, colWidths=[2.5*inch, 4*inch])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(details_table)
        story.append(Spacer(1, 0.3*inch))

        # Forecast Visualization
        story.append(Paragraph("Forecast Visualization", heading_style))
        
        forecast_chart = ReportGenerationService._create_forecast_chart(prediction_record)
        if forecast_chart:
            story.append(forecast_chart)
            story.append(Spacer(1, 0.2*inch))

        # Model Performance Metrics
        story.append(Paragraph("Model Performance Metrics", heading_style))
        
        accuracy_snapshot = prediction_record.get('model_accuracy_snapshot', {})
        if isinstance(accuracy_snapshot, dict):
            metrics_data = [
                ['Metric', 'Value', 'Interpretation']
            ]
            
            mape = accuracy_snapshot.get('mape', 0)
            r2 = accuracy_snapshot.get('r2', 0)
            rmse = accuracy_snapshot.get('rmse', 0)
            mae = accuracy_snapshot.get('mae', 0)
            
            metrics_data.extend([
                ['MAPE', f'{mape:.2f}%', ReportGenerationService._interpret_mape(mape)],
                ['R² Score', f'{r2:.4f}', ReportGenerationService._interpret_r2(r2)],
                ['RMSE', f'{rmse:.4f}', 'Lower is better'],
                ['MAE', f'{mae:.4f}', 'Lower is better'],
            ])
            
            metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.8*inch, 3*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 0.3*inch))

        # Metrics Bar Chart
        metrics_chart = ReportGenerationService._create_metrics_chart(accuracy_snapshot)
        if metrics_chart:
            story.append(metrics_chart)
            story.append(Spacer(1, 0.3*inch))

        # Technical Analysis
        story.append(Paragraph("Technical Analysis", heading_style))
        technical_analysis = insights.get('technical_analysis', 'No technical analysis available.')
        story.append(Paragraph(technical_analysis, body_style))
        story.append(Spacer(1, 0.2*inch))

        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))
        recommendations = insights.get('recommendations', 'No recommendations available.')
        story.append(Paragraph(recommendations, body_style))
        story.append(Spacer(1, 0.3*inch))

        # Page Break before footer information
        story.append(PageBreak())

        # Additional Metadata
        story.append(Paragraph("Additional Information", heading_style))
        
        if prediction_record.get('aggregation_participants'):
            story.append(Paragraph(
                f"<b>Federated Learning:</b> This prediction used a model trained collaboratively "
                f"by {prediction_record['aggregation_participants']} participating hospitals.",
                body_style
            ))
        
        if prediction_record.get('dp_epsilon_used'):
            story.append(Paragraph(
                f"<b>Privacy Protection:</b> Differential privacy with ε = {prediction_record['dp_epsilon_used']:.2f}",
                body_style
            ))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"<b>Prediction Hash:</b> {prediction_record.get('prediction_hash', 'N/A')[:32]}...",
            body_style
        ))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=colors.grey)
        story.append(Paragraph(
            "This report is generated by the Federated Healthcare Intelligence Platform. "
            "For questions, contact your system administrator.",
            footer_style
        ))

        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Optionally save to file
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

        return pdf_bytes

    @staticmethod
    def _create_forecast_chart(prediction_record: Dict[str, Any]) -> Optional[Image]:
        """Create forecast visualization chart"""
        try:
            forecast_data = prediction_record.get('forecast_data', {})
            
            if not isinstance(forecast_data, dict):
                return None
            
            # Extract forecast horizons
            horizon_forecasts = forecast_data.get('horizon_forecasts', {})
            if not horizon_forecasts:
                forecasts = forecast_data.get('forecasts', [])
                if forecasts:
                    hours = [f['hour_ahead'] for f in forecasts]
                    predictions = [f['prediction'] for f in forecasts]
                    lower_bounds = [f.get('lower_bound', f['prediction'] * 0.9) for f in forecasts]
                    upper_bounds = [f.get('upper_bound', f['prediction'] * 1.1) for f in forecasts]
                else:
                    return None
            else:
                hours = [int(k.replace('h', '')) for k in horizon_forecasts.keys()]
                predictions = [horizon_forecasts[k]['prediction'] for k in horizon_forecasts.keys()]
                lower_bounds = [horizon_forecasts[k].get('lower_bound', horizon_forecasts[k]['prediction'] * 0.9) 
                               for k in horizon_forecasts.keys()]
                upper_bounds = [horizon_forecasts[k].get('upper_bound', horizon_forecasts[k]['prediction'] * 1.1) 
                               for k in horizon_forecasts.keys()]

            # Create plot
            fig, ax = plt.subplots(figsize=(8, 4))
            
            ax.plot(hours, predictions, 'o-', color='#1e40af', linewidth=2, markersize=6, label='Prediction')
            ax.fill_between(hours, lower_bounds, upper_bounds, alpha=0.3, color='#60a5fa', label='Confidence Interval')
            
            ax.set_xlabel('Forecast Horizon (hours)', fontsize=11)
            ax.set_ylabel('Predicted Value', fontsize=11)
            ax.set_title('Multi-Horizon Forecast', fontsize=13, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=6*inch, height=3*inch)
            return img
            
        except Exception as e:
            print(f"[REPORT] Failed to create forecast chart: {str(e)}")
            return None

    @staticmethod
    def _create_metrics_chart(metrics: Dict[str, float]) -> Optional[Image]:
        """Create bar chart for performance metrics"""
        try:
            if not metrics or not isinstance(metrics, dict):
                return None
            
            # Extract key metrics
            metric_names = []
            metric_values = []
            
            if 'mape' in metrics and metrics['mape'] is not None:
                metric_names.append('MAPE (%)')
                metric_values.append(metrics['mape'])
            
            if 'r2' in metrics and metrics['r2'] is not None:
                metric_names.append('R² × 100')
                metric_values.append(metrics['r2'] * 100)  # Scale for visibility
            
            if 'mae' in metrics and metrics['mae'] is not None:
                metric_names.append('MAE')
                metric_values.append(metrics['mae'])
            
            if 'rmse' in metrics and metrics['rmse'] is not None:
                metric_names.append('RMSE')
                metric_values.append(metrics['rmse'])
            
            if not metric_names:
                return None
            
            # Create bar chart
            fig, ax = plt.subplots(figsize=(7, 3.5))
            
            colors_list = ['#1e40af', '#10b981', '#f59e0b', '#ef4444']
            bars = ax.bar(metric_names, metric_values, color=colors_list[:len(metric_names)], alpha=0.8)
            
            ax.set_ylabel('Value', fontsize=11)
            ax.set_title('Performance Metrics Overview', fontsize=13, fontweight='bold')
            ax.grid(True, axis='y', alpha=0.3)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.2f}',
                       ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image
            img = Image(img_buffer, width=5.5*inch, height=2.75*inch)
            return img
            
        except Exception as e:
            print(f"[REPORT] Failed to create metrics chart: {str(e)}")
            return None

    @staticmethod
    def _interpret_mape(mape: float) -> str:
        """Interpret MAPE value"""
        if mape < 10:
            return "Excellent"
        elif mape < 20:
            return "Good"
        elif mape < 30:
            return "Acceptable"
        else:
            return "Needs Improvement"

    @staticmethod
    def _interpret_r2(r2: float) -> str:
        """Interpret R² value"""
        if r2 > 0.9:
            return "Excellent fit"
        elif r2 > 0.7:
            return "Good fit"
        elif r2 > 0.5:
            return "Moderate fit"
        else:
            return "Weak fit"
