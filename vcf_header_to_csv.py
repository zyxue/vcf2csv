import os
import sys
import gzip

import numpy as np
import pandas as pd


def split_header_val_str(val_str):
    val_str = val_str.strip('<').strip('>')
    in_q = False                # inside quotes or not
    sub_str_list = []
    sub_str = []
    for i in val_str:
        if i == '"':
            in_q = not in_q     # flip in_q
        elif i == ',':
            if in_q:
                sub_str.append(i)
            else:
                sub_str_list.append(''.join(sub_str))
                sub_str = []
        else:
            sub_str.append(i)
    sub_str_list.append(''.join(sub_str))
    return sub_str_list


# https://gist.github.com/dceoy/99d976a2c01e7f0ba1c813778f9db744 
def read_vcf_header(path, target_keys=None):
    dd = {}
    cur_key = None
    with gzip.open(path, 'rt') as f:
        for line in f:
            if not line.startswith('##'):
                break

            key, val_str = line.strip().replace('##', '').split('=', maxsplit=1)
            if target_keys is not None and key not in target_keys:
                continue

            if cur_key is None:
                cur_key, res = key, []
            else:
                if key != cur_key:
                    dd[cur_key] = res
                    cur_key, res = key, []

            vals = split_header_val_str(val_str)
            vals.insert(0, cur_key)
            res.append(vals)

        dd[cur_key] = res
        return dd


if __name__ == "__main__":

    vcf_path = sys.argv[1]
    header_dd = read_vcf_header(vcf_path, target_keys=['FILTER', 'FORMAT'])

    for key, rows in header_dd.items():
        csv_hdrs, csv_rows = [], []
        # [1:] ignore the first element, which is the key
        for row in rows:
            csv_hdr, csv_row = [], []
            for cell in row[1:]:
                h, v = cell.split('=', maxsplit=1)
                csv_hdr.append(h)
                csv_row.append(v)
            csv_hdrs.append(tuple(csv_hdr))
            csv_rows.append(csv_row)

        try:
            assert len(set(csv_hdrs)) == 1
        except AssertionError:
            print(f'multiple headers found for {key}: {set(csv_hdr_list)}')

        df = pd.DataFrame(csv_rows, columns=csv_hdrs[0])
        cols = ['key'] + list(csv_hdrs[0])
        df['key'] = key
        df = df[cols]
        out = os.path.join(
            os.path.dirname(vcf_path),
            f'{vcf_path}.{key}.csv'
        )
        df.to_csv(out, index=False)
        print(df)
        print()

