import pyexcel, os
fixture_file = 'bad-headers-Root.csv'
filename = os.path.join(os.path.dirname(__file__), 'fixtures', fixture_file)
sv_worksheet = pyexcel.get_sheet(file_name=filename, skip_empty_rows=False)
for sv_row in sv_worksheet.row:
    print('sv_row', list(sv_row))
