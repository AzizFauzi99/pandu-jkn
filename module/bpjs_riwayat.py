from datetime import date

from utils.db import run_select

kode_layanan_rs = {"semua": None, "rawat_jalan_rs": 1, "rawat_inap_rs": 2}


def _susun_kunjungan(data: list[dict]):
    return {
        "total_kunjungan": data[0]["total"] if data else 0,
        "kunjungan": [{k: v for k, v in row.items() if k != "total"} for row in data],
    }


def _kunjungan_faskes_pertama(user_nik: str, dari: date | None, sampai: date | None, jumlah: int):
    return _susun_kunjungan(
        run_select(
            """
            select k.fkp03::text as tanggal,
                   jenis.label_text as jenis_kunjungan,
                   k.fkp15 as diagnosis,
                   k.fkp15a as keterangan,
                   pulang.label_text as status_pulang,
                   count(*) over () as total
            from bpjs_fktpkapitasi k
            left join bpjs_metadata_lookup jenis
                   on jenis.variable_name = 'FKP22' and jenis.code_value = k.fkp22
            left join bpjs_metadata_lookup pulang
                   on pulang.variable_name = 'FKP13' and pulang.code_value = k.fkp13
            where k.pstv01 = %s
              and (%s::date is null or k.fkp03 >= %s::date)
              and (%s::date is null or k.fkp03 <= %s::date)
            order by k.fkp03 desc
            limit %s
            """,
            (int(user_nik), dari, dari, sampai, sampai, jumlah),
            limit=jumlah,
        )
    )


def _kunjungan_rumah_sakit(
    user_nik: str, kode_layanan: int | None, dari: date | None, sampai: date | None, jumlah: int
):
    return _susun_kunjungan(
        run_select(
            """
            select k.fkl03::text as tanggal_masuk,
                   k.fkl04::text as tanggal_pulang,
                   (k.fkl04 - k.fkl03) as lama_rawat_hari,
                   layanan.label_text as layanan,
                   k.fkl17a as kode_diagnosis,
                   k.fkl18a as diagnosis,
                   (select array_agg(d.fkl24b order by d.fkl24a)
                    from bpjs_diagnosissekunder d
                    where d.fkl02 = k.fkl02) as diagnosis_sekunder,
                   keluar.label_text as status_keluar,
                   k.fkl48 as biaya_rupiah,
                   count(*) over () as total
            from bpjs_fkrtl k
            left join bpjs_metadata_lookup layanan
                   on layanan.variable_name = 'FKL10' and layanan.code_value = k.fkl10
            left join bpjs_metadata_lookup keluar
                   on keluar.variable_name = 'FKL14' and keluar.code_value = k.fkl14
            where k.pstv01 = %s
              and (%s::date is null or k.fkl03 >= %s::date)
              and (%s::date is null or k.fkl03 <= %s::date)
              and (%s::int is null or k.fkl10 = %s::int)
            order by k.fkl03 desc
            limit %s
            """,
            (int(user_nik), dari, dari, sampai, sampai, kode_layanan, kode_layanan, jumlah),
            limit=jumlah,
        )
    )


def kunjungan_pengguna(
    user_nik: str, layanan: str, dari_tanggal: str | None, sampai_tanggal: str | None, jumlah: int
):
    try:
        dari = date.fromisoformat(dari_tanggal) if dari_tanggal else None
        sampai = date.fromisoformat(sampai_tanggal) if sampai_tanggal else None
    except ValueError:
        return {
            "error": "Format tanggal tidak valid.",
            "saran": "Tulis tanggal sebagai YYYY-MM-DD, misalnya 2024-10-01.",
        }
    jumlah = max(1, min(jumlah, 30))

    hasil = {}
    if layanan in ("semua", "faskes_pertama"):
        hasil["faskes_pertama"] = _kunjungan_faskes_pertama(user_nik, dari, sampai, jumlah)
    if layanan != "faskes_pertama":
        hasil["rumah_sakit"] = _kunjungan_rumah_sakit(
            user_nik, kode_layanan_rs[layanan], dari, sampai, jumlah
        )
    return hasil


def ringkasan_diagnosis(user_nik: str):
    faskes_data = run_select(
        """
        select fkp15 as diagnosis, count(*) as jumlah_kunjungan
        from bpjs_fktpkapitasi
        where pstv01 = %s and fkp15 is not null
        group by fkp15
        order by jumlah_kunjungan desc
        limit 5
        """,
        (int(user_nik),),
    )
    rumah_sakit_data = run_select(
        """
        select fkl17a as kode_diagnosis, fkl18a as diagnosis, count(*) as jumlah_kunjungan
        from bpjs_fkrtl
        where pstv01 = %s and fkl18a is not null
        group by fkl17a, fkl18a
        order by jumlah_kunjungan desc
        limit 5
        """,
        (int(user_nik),),
    )
    sekunder_data = run_select(
        """
        select d.fkl24b as diagnosis, count(*) as jumlah_kunjungan
        from bpjs_fkrtl k
        join bpjs_diagnosissekunder d on d.fkl02 = k.fkl02
        where k.pstv01 = %s and d.fkl24b is not null
        group by d.fkl24b
        order by jumlah_kunjungan desc
        limit 5
        """,
        (int(user_nik),),
    )
    return {
        "faskes_pertama": faskes_data,
        "rumah_sakit": rumah_sakit_data,
        "diagnosis_sekunder": sekunder_data,
    }


def biaya_klaim(user_nik: str):
    rumah_sakit_data = run_select(
        """
        select layanan.label_text as layanan,
               count(*) as jumlah_kunjungan,
               sum(k.fkl48) as total_biaya
        from bpjs_fkrtl k
        left join bpjs_metadata_lookup layanan
               on layanan.variable_name = 'FKL10' and layanan.code_value = k.fkl10
        where k.pstv01 = %s
        group by layanan.label_text
        order by layanan.label_text
        """,
        (int(user_nik),),
    )
    non_kapitasi_data = run_select(
        """
        select count(*) as jumlah_kunjungan,
               coalesce(sum(pnk18), 0) as total_biaya
        from bpjs_nonkapitasi
        where pstv01 = %s
        """,
        (int(user_nik),),
    )[0]

    total_biaya = non_kapitasi_data["total_biaya"] + sum(
        row["total_biaya"] for row in rumah_sakit_data
    )
    return {
        "total_biaya_rupiah": total_biaya,
        "rumah_sakit": rumah_sakit_data,
        "non_kapitasi": non_kapitasi_data,
        "catatan": "Biaya riil yang dibayar BPJS. Faskes tingkat pertama dibayar kapitasi, jadi tidak ada nominal per kunjungan.",
    }
