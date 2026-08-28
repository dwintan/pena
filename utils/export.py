import io
import pandas as pd


def to_excel(df):

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Fenomena"
        )

        worksheet = writer.sheets["Fenomena"]

        # Lebar kolom
        for column_cells in worksheet.columns:

            max_length = 0

            column_letter = column_cells[0].column_letter

            for cell in column_cells:

                try:
                    cell_length = len(
                        str(cell.value)
                    )

                    if cell_length > max_length:
                        max_length = cell_length

                except Exception:
                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = min(
                max_length + 2,
                60
            )

    output.seek(0)

    return output.getvalue()