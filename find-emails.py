import pandas as pd
import streamlit as st

pd.set_option('future.no_silent_downcasting', True)

st.title('Combine Adopters, Fosters, and Donors Email Lists')

st.header('Instructions')

with st.expander('How to export the Adopter file from Shelterluv'):
    st.markdown("""
1. Log in to Shelterluv: https://new.shelterluv.com/reports?section=adoption
2. Update the date range to the desired period (e.g., last month, last year).
3. Click "Run Report". This will open up a new tab with the report results.
4. In the new tab, click the "Excel" button to download the report as an Excel file. This will automatically download a file to your computer.
5. Drop that file into the "Adopter file" uploader below.

""")

with st.expander('How to export the Foster file from Shelterluv'):
    st.markdown("""
1. Log in to Shelterluv and navigate to the foster report section: https://new.shelterluv.com/reports?section=foster
2. For the "Foster Activity" report, update the date range to the desired period (e.g., last month, last year).
3. Click "Run Report" on the "Foster Activity" report. This will open up a new tab with the report results.
4. In the new tab, click the "Excel" button to download the report as an Excel file. This will automatically download a file to your computer.
5. Drop that file into the "Foster file" uploader below.
""")

with st.expander('How to export the Donor file from Zeffy'):
    st.markdown("""
1. Log in to Zeffy: https://app.zeffy.com/
2. Navigate to the "Payments" section.
3. Click "Export" in the top right corner of the page.
4. Confirm that "First Name", "Last Name", "Email", and "Campaign Title" are selected in the export options, then click "Export". This will automatically download a file to your computer.
6. Drop that file into the "Donor file" uploader below.
""")

st.header('Upload Files')

existingFile = st.file_uploader('Upload existing combined file (optional)', type=['csv', 'xlsx', 'xls'])
adopterFile = st.file_uploader('Upload Adopter file', type=['xlsx', 'xls'])
fosterFile = st.file_uploader('Upload Foster file', type=['xlsx', 'xls'])
donorFile = st.file_uploader('Upload Donor file', type=['xlsx', 'xls'])

if st.button('Combine'):
    if not adopterFile or not fosterFile or not donorFile:
        st.error('Please upload all three files.')
    else:
        try:
            parsedAdopters = pd.read_excel(adopterFile, sheet_name="Worksheet").drop_duplicates(subset=['Primary Email'], keep='first')
            parsedAdopters['First Name'] = parsedAdopters['Adopter Name'].apply(lambda x: x.split()[0] if pd.notna(x) and len(x.split()) >= 1 else '')
            parsedAdopters['Last Name'] = parsedAdopters['Adopter Name'].apply(lambda x: x.split()[-1] if pd.notna(x) and len(x.split()) >= 2 else '')
            parsedAdopters['isAdopter'] = True
            st.write(f'Adopters loaded: {len(parsedAdopters)}')
        except (ValueError, KeyError) as e:
            st.error(f'Adopter file has the wrong format. Make sure it has a "Worksheet" sheet with "Primary Email" and "Adopter Name" columns. Error: {e}')
            st.stop()

        try:
            parsedFosters = pd.read_excel(fosterFile, sheet_name="Worksheet").drop_duplicates(subset=['Foster Person Email'], keep='first')
            parsedFosters = parsedFosters.rename(columns={'Foster Person Email': 'Primary Email'})
            parsedFosters['First Name'] = parsedFosters['Foster Person Name'].apply(lambda x: x.split()[0] if pd.notna(x) and len(x.split()) >= 1 else '')
            parsedFosters['Last Name'] = parsedFosters['Foster Person Name'].apply(lambda x: x.split()[-1] if pd.notna(x) and len(x.split()) >= 2 else '')
            parsedFosters['isFoster'] = True
            st.write(f'Fosters loaded: {len(parsedFosters)}')
        except (ValueError, KeyError) as e:
            st.error(f'Foster file has the wrong format. Make sure it has a "Worksheet" sheet with "Foster Person Email" and "Foster Person Name" columns. Error: {e}')
            st.stop()

        try:
            parsedDonors = pd.read_excel(donorFile, sheet_name="Export")
            parsedDonors = parsedDonors.rename(columns={'Email': 'Primary Email'})
            parsedDonors['First Name'] = parsedDonors['First Name'].fillna('')
            parsedDonors['Last Name'] = parsedDonors['Last Name'].fillna('')
            parsedDonors['isDonor'] = True
            st.write(f'Donors loaded: {len(parsedDonors)}')
        except (ValueError, KeyError) as e:
            st.error(f'Donor file has the wrong format. Make sure it has an "Export" sheet with "Email", "First Name", and "Last Name" columns. Error: {e}')
            st.stop()

        if existingFile:
            try:
                if existingFile.name.endswith('.csv'):
                    existing = pd.read_csv(existingFile)
                else:
                    existing = pd.read_excel(existingFile)
            except Exception as e:
                st.error(f'Could not read existing file. Error: {e}')
                st.stop()
        else:
            existing = pd.DataFrame()
        existingCount = len(existing) if not existing.empty else 0

        combinedData = pd.concat([existing, parsedAdopters, parsedFosters, parsedDonors], ignore_index=True)
        combinedData['Campaign Title'] = combinedData['Campaign Title'].fillna('')
        combinedData['isAdopter'] = combinedData['isAdopter'].fillna(False)
        combinedData['isFoster'] = combinedData['isFoster'].fillna(False)
        combinedData['isDonor'] = combinedData['isDonor'].fillna(False)
        combinedData = combinedData.groupby('Primary Email', dropna=True).agg({
            'First Name': 'first',
            'Last Name': 'first',
            'isAdopter': 'max',
            'isFoster': 'max',
            'isDonor': 'max',
            'Campaign Title': lambda x: ', '.join(sorted(set(v for v in x if v)))
        }).reset_index()

        st.write(f'Previously in file: {existingCount}')
        st.write(f'Total after merge: {len(combinedData)}')
        st.write(f'New contacts added: {len(combinedData) - existingCount}')

        st.dataframe(combinedData)

        csv = combinedData.to_csv(index=False)
        st.download_button('Download CSV', csv, 'combined_adopters_fosters_donors.csv', 'text/csv')
