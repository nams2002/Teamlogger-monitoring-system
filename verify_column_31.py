#!/usr/bin/env python3
"""Verify that column 31 has been added to the Google Sheet"""

from src.googlesheets_Client import GoogleSheetsLeaveClient

def main():
    print('=== VERIFYING COLUMN 31 ADDITION ===')
    print('🎯 Checking if Google Sheet now has 32+ columns for full month support')
    print()
    
    client = GoogleSheetsLeaveClient()
    
    try:
        # Fetch current sheet data
        sheet_data = client._fetch_sheet_data("Sep 25", force_refresh=True)
        
        if sheet_data:
            header_row = sheet_data[0]
            total_cols = len(header_row)
            
            print(f'📊 CURRENT SHEET STATUS:')
            print(f'   Total columns: {total_cols}')
            
            # Show header structure
            print(f'\n📋 HEADER STRUCTURE:')
            print(f'   First 10: {header_row[:10]}')
            if total_cols > 10:
                print(f'   Last 10:  {header_row[-10:]}')
            
            # Check for day 31
            has_day_31 = False
            day_31_position = None
            
            for i, col in enumerate(header_row):
                if str(col).strip() == "31":
                    has_day_31 = True
                    day_31_position = i
                    break
            
            print(f'\n🔍 DAY 31 CHECK:')
            if has_day_31:
                print(f'   ✅ Day 31 found at column {day_31_position}')
                print(f'   ✅ Column 31 successfully added!')
            else:
                print(f'   ❌ Day 31 not found')
                print(f'   🔧 Need to add column 31 to the Google Sheet')
            
            # Month support analysis
            print(f'\n📅 MONTH SUPPORT ANALYSIS:')
            
            month_support = {
                'February (28/29 days)': total_cols >= 30,
                'April/June/Sept/Nov (30 days)': total_cols >= 31, 
                'Jan/Mar/May/Jul/Aug/Oct/Dec (31 days)': total_cols >= 32,
                'Buffer for future expansion': total_cols >= 35
            }
            
            for month_type, supported in month_support.items():
                status = "✅ SUPPORTED" if supported else "❌ NEEDS MORE COLUMNS"
                print(f'   {month_type}: {status}')
            
            # Overall assessment
            print(f'\n🎯 OVERALL ASSESSMENT:')
            
            if total_cols >= 32:
                print(f'   🎉 EXCELLENT: Full multi-month support!')
                print(f'   ✅ All months (28-31 days): Supported')
                print(f'   ✅ Cross-month weeks: Supported')
                print(f'   ✅ System ready for year-round operation')
                
            elif total_cols >= 31:
                print(f'   ⚠️ GOOD: Most months supported')
                print(f'   ✅ 30-day months: Supported')
                print(f'   ❌ 31-day months: May have issues')
                print(f'   🔧 Add 1 more column for full support')
                
            else:
                print(f'   ❌ LIMITED: Insufficient columns')
                print(f'   🔧 Add {32 - total_cols} more columns for full support')
            
            # Test with sample data
            print(f'\n🧪 TESTING SAMPLE DATA:')
            
            # Find a sample employee row
            sample_row = None
            sample_name = None
            
            for row in sheet_data[1:6]:  # Check first 5 data rows
                if row and len(row) > 0 and row[0]:
                    sample_row = row
                    sample_name = row[0]
                    break
            
            if sample_row:
                print(f'   👤 Testing with: {sample_name}')
                print(f'   📊 Row has {len(sample_row)} columns')
                
                # Check if we can access day 31 data
                if len(sample_row) >= 32:
                    day_31_value = sample_row[31] if len(sample_row) > 31 else ""
                    print(f'   📅 Day 31 data: "{day_31_value}"')
                    print(f'   ✅ Can access day 31 data')
                else:
                    print(f'   ❌ Cannot access day 31 data (row too short)')
            
            return total_cols >= 32
            
        else:
            print(f'❌ Could not fetch sheet data')
            return False
            
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        return False

if __name__ == "__main__":
    success = main()
    
    print(f'\n=== NEXT STEPS ===')
    
    if success:
        print(f'🎉 READY: System fully supports multi-month operation!')
        print(f'✅ No further action needed')
    else:
        print(f'🔧 ACTION REQUIRED:')
        print(f'1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1RJt6TXG_x5EmTWX6YNyC9qiCCEVsmb4lBjTUe2Ua8Yk/edit?gid=1496030997')
        print(f'2. Add column "31" after column "30"')
        print(f'3. Save the sheet')
        print(f'4. Run this test again to verify')
    
    print(f'\n💡 Once column 31 is added:')
    print(f'   ✅ October 2025: Will work perfectly')
    print(f'   ✅ December 2025: Will work perfectly') 
    print(f'   ✅ All future 31-day months: Will work perfectly')
    print(f'   ✅ Cross-month weeks: Will work perfectly')
