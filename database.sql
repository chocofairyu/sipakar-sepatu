-- ============================================================
-- Sistem Pakar Penentuan Metode Pencucian Sepatu
-- Menggunakan Metode Certainty Factor (CF)
-- ============================================================

CREATE DATABASE IF NOT EXISTS db_sepatu_cf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE db_sepatu_cf;

-- ------------------------------------------------------------
-- Tabel jenis bahan sepatu
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_bahan (
    id_bahan    INT PRIMARY KEY AUTO_INCREMENT,
    nama_bahan  VARCHAR(50) NOT NULL,
    deskripsi   TEXT
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Tabel jenis noda
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_noda (
    id_noda     INT PRIMARY KEY AUTO_INCREMENT,
    nama_noda   VARCHAR(50) NOT NULL,
    deskripsi   TEXT
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Tabel metode pencucian
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_metode (
    id_metode   INT PRIMARY KEY AUTO_INCREMENT,
    nama_metode VARCHAR(100) NOT NULL,
    deskripsi   TEXT
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Tabel aturan (basis pengetahuan)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_aturan (
    id_aturan   INT PRIMARY KEY AUTO_INCREMENT,
    id_bahan    INT NOT NULL,
    id_noda     INT NOT NULL,
    id_metode   INT NOT NULL,
    cf_pakar    DECIMAL(3,2) NOT NULL COMMENT 'Nilai CF dari pakar (0.0 - 1.0)',
    catatan     TEXT,
    FOREIGN KEY (id_bahan)  REFERENCES tb_bahan(id_bahan),
    FOREIGN KEY (id_noda)   REFERENCES tb_noda(id_noda),
    FOREIGN KEY (id_metode) REFERENCES tb_metode(id_metode)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Tabel riwayat konsultasi
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_konsultasi (
    id_konsultasi   INT PRIMARY KEY AUTO_INCREMENT,
    nama_pengguna   VARCHAR(100),
    id_bahan        INT NOT NULL,
    id_noda         INT NOT NULL,
    cf_user         DECIMAL(3,2) NOT NULL COMMENT 'Nilai keyakinan pengguna (0.0 - 1.0)',
    id_metode_hasil INT NOT NULL,
    cf_akhir        DECIMAL(5,4) NOT NULL COMMENT 'Nilai CF akhir hasil perhitungan',
    tanggal         DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_bahan)        REFERENCES tb_bahan(id_bahan),
    FOREIGN KEY (id_noda)         REFERENCES tb_noda(id_noda),
    FOREIGN KEY (id_metode_hasil) REFERENCES tb_metode(id_metode)
) ENGINE=InnoDB;


-- ============================================================
-- DATA: Jenis Bahan Sepatu
-- ============================================================
INSERT INTO tb_bahan (nama_bahan, deskripsi) VALUES
('Kulit Asli',        'Material dari kulit hewan asli, pori alami, sensitif terhadap air dan bahan kimia keras'),
('Kulit Sintetis',    'Material buatan berbasis PU/PVC, lebih tahan air dibanding kulit asli, permukaan non-pori'),
('Kanvas',            'Material kain tenun berbasis katun/polyester, cukup tahan pencucian basah'),
('Suede',             'Material kulit dengan permukaan beludru berbulu, sangat sensitif terhadap air'),
('Mesh / Rajut',      'Material rajutan berpori untuk ventilasi, minyak mudah meresap ke serat'),
('Rubber / Karet (Sol)', 'Material sol karet, tahan air dan sabun, paling mudah dibersihkan'),
('Nubuck',            'Material kulit amplas halus mirip suede, sensitif terhadap air berlebih'),
('Satin',             'Material kain mengkilap halus, sangat rentan terhadap gosokan dan bahan kimia');


-- ============================================================
-- DATA: Jenis Noda
-- ============================================================
INSERT INTO tb_noda (nama_noda, deskripsi) VALUES
('Minyak / Lemak',       'Noda berminyak dari pelumas, makanan berminyak, atau lemak lainnya'),
('Lumpur / Tanah',       'Noda tanah atau lumpur, paling umum ditemui sehari-hari'),
('Darah',                'Noda protein darah, gunakan air dingin, air panas membuat protein mengikat'),
('Tinta',                'Noda tinta bolpoin atau spidol, membandel dan sulit dihilangkan'),
('Jamur / Lumut',        'Noda biologis yang tumbuh pada kondisi lembab, butuh cairan antijamur'),
('Makanan / Minuman',    'Noda dari sisa makanan atau minuman yang tumpah'),
('Cat',                  'Noda cat tembok atau cat sepatu, sangat sulit bila sudah kering'),
('Karat',                'Noda oksidasi logam yang menempel pada sepatu'),
('Debu Ringan',          'Kotoran debu tipis di permukaan, penanganan paling mudah');


-- ============================================================
-- DATA: Metode Pencucian
-- ============================================================
INSERT INTO tb_metode (nama_metode, deskripsi) VALUES
('Cuci Tangan Manual dengan Sabun',             'Sikat lembut dibasahi air dan sabun khusus sepatu, gosok perlahan searah serat, bilas, keringkan di tempat teduh berangin'),
('Deep Clean dengan Sikat Halus',               'Pencucian menyeluruh memakai sikat berbulu halus dan campuran sabun, menjangkau sela jahitan dan sol untuk kotoran membandel'),
('Dry Clean / Cairan Khusus',                   'Menggunakan cairan pembersih khusus tanpa air berlebih, cocok untuk material sensitif seperti satin dan nubuck'),
('Rendam Air Dingin',                           'Sepatu direndam singkat di air dingin bersabun untuk melunakkan kotoran sebelum disikat, cocok untuk kanvas/mesh'),
('Spot Cleaning (Setempat)',                    'Membersihkan hanya area bernoda menggunakan kain/cotton bud dan cairan pembersih, tanpa mencuci seluruh sepatu'),
('Sikat Kering',                                'Menyikat kotoran kering (lumpur, debu) tanpa air terlebih dahulu agar tidak menyebar dan meresap ke material'),
('Lap Lembab',                                  'Mengelap permukaan dengan kain lembab untuk debu ringan atau noda permukaan yang tidak memerlukan pencucian penuh'),
('Steam Cleaning',                              'Uap panas digunakan untuk melonggarkan kotoran dan membunuh bakteri/jamur pada material yang cukup tahan panas'),
('Pembersih Suede',                             'Sikat khusus suede dan penghapus (eraser) digunakan untuk mengangkat noda tanpa merusak tekstur berbulu material'),
('Pembersih Kimia (Solvent)',                   'Solvent dioleskan dengan kapas/cotton bud secara presisi pada noda membandel seperti tinta, cat, atau minyak'),
('Pembersih Enzimatik',                         'Cairan enzim diaplikasikan untuk memecah noda organik (darah, protein) lalu dilap dengan kain bersih dan air dingin'),
('Mesin Cuci Gentle',                           'Dicuci dengan mode gentle dan suhu rendah, hanya untuk kanvas/mesh tertentu yang benar-benar tahan air');


-- ============================================================
-- DATA: Basis Pengetahuan — 72 Aturan (Bahan x Noda x Metode)
-- ============================================================
-- Format: (id_bahan, id_noda, id_metode, cf_pakar, catatan)
-- Bahan  : 1=Kulit Asli, 2=Kulit Sintetis, 3=Kanvas, 4=Suede,
--           5=Mesh/Rajut, 6=Rubber/Karet, 7=Nubuck, 8=Satin
-- Noda   : 1=Minyak, 2=Lumpur, 3=Darah, 4=Tinta, 5=Jamur,
--           6=Makanan, 7=Cat, 8=Karat, 9=Debu
-- Metode : 1=Cuci Manual, 2=Deep Clean, 3=Dry Clean, 4=Rendam,
--           5=Spot Clean, 6=Sikat Kering, 7=Lap Lembab,
--           8=Steam, 9=Pembersih Suede, 10=Pembersih Kimia,
--           11=Enzimatik, 12=Mesin Gentle

INSERT INTO tb_aturan (id_bahan, id_noda, id_metode, cf_pakar, catatan) VALUES
-- === KULIT ASLI ===
(1, 1, 10, 0.7, 'Solvent ringan agar pori kulit tidak rusak; hindari air berlebih'),
(1, 2,  6, 0.8, 'Tunggu lumpur kering dulu sebelum disikat agar tidak menyebar'),
(1, 3, 11, 0.7, 'Gunakan air dingin, air panas membuat protein darah mengikat'),
(1, 4, 10, 0.6, 'Tinta membandel pada kulit, hasil tidak selalu tuntas'),
(1, 5,  7, 0.7, 'Lap dengan cairan anti jamur khusus kulit, lalu keringkan natural'),
(1, 6,  5, 0.8, 'Bersihkan segera sebelum noda meresap ke pori kulit'),
(1, 7, 10, 0.5, 'Cat yang sudah kering sangat sulit dihilangkan tanpa merusak warna kulit'),
(1, 8,  5, 0.5, 'Karat jarang menempel di kulit asli; bila ada, perlu kehati-hatian ekstra'),
(1, 9,  7, 0.9, 'Cukup dilap, perawatan paling ringan dan rutin'),

-- === KULIT SINTETIS ===
(2, 1,  1, 0.7, 'Material lebih tahan air dibanding kulit asli'),
(2, 2,  6, 0.7, 'Sikat setelah kering, lanjut lap basah bila masih ada sisa'),
(2, 3, 11, 0.7, 'Sama seperti kulit asli, hindari air panas'),
(2, 4, 10, 0.6, 'Cek dulu di area kecil agar warna tidak luntur'),
(2, 5,  7, 0.7, 'Material sintetis lebih mudah dibersihkan dari jamur dibanding kulit asli'),
(2, 6,  5, 0.8, 'Noda umumnya tidak meresap dalam karena permukaan non-pori'),
(2, 7, 10, 0.6, 'Lebih aman dibanding pada kulit asli karena tidak ada pori alami'),
(2, 8,  1, 0.5, 'Jarang terjadi; cukup dibersihkan manual'),
(2, 9,  7, 0.9, 'Perawatan ringan rutin'),

-- === KANVAS ===
(3, 1,  2, 0.7, 'Gunakan sabun cuci kain agar minyak terangkat dari serat'),
(3, 2,  4, 0.8, 'Rendam dulu agar lumpur larut sebelum disikat'),
(3, 3, 11, 0.8, 'Enzim efektif pada serat kain seperti kanvas'),
(3, 4, 10, 0.6, 'Tinta menyerap ke serat kain, hasil bervariasi'),
(3, 5,  2, 0.7, 'Sikat dengan campuran sabun antijamur'),
(3, 6,  1, 0.8, 'Material kanvas tahan terhadap pencucian basah'),
(3, 7, 10, 0.5, 'Bila cat sudah kering dan mengeras, sulit terangkat total'),
(3, 8,  2, 0.6, 'Sikat dengan sabun, ulangi beberapa kali untuk hasil maksimal'),
(3, 9,  6, 0.9, 'Cukup disikat kering tanpa air'),

-- === SUEDE ===
(4, 1,  9, 0.7, 'Gunakan bedak/tepung jagung untuk menyerap minyak sebelum disikat'),
(4, 2,  6, 0.8, 'Tunggu kering, sikat searah serat suede'),
(4, 3,  9, 0.6, 'Suede sensitif terhadap air, hasil tidak selalu sempurna'),
(4, 4,  9, 0.4, 'Suede sangat sulit dibersihkan dari tinta, risiko merusak tekstur tinggi'),
(4, 5,  9, 0.6, 'Gunakan sikat khusus suede dan cairan anti jamur ringan'),
(4, 6,  5, 0.6, 'Tepuk-tepuk dengan kain kering dulu sebelum memakai cairan'),
(4, 7,  3, 0.3, 'Sangat berisiko; sebaiknya dirujuk ke profesional'),
(4, 8,  9, 0.4, 'Jarang terjadi dan cukup sulit ditangani'),
(4, 9,  6, 0.9, 'Perawatan rutin paling aman untuk suede'),

-- === MESH / RAJUT ===
(5, 1,  1, 0.7, 'Material berpori, minyak mudah meresap ke serat'),
(5, 2,  4, 0.8, 'Rendam dan kucek lembut agar lumpur lepas dari rajutan'),
(5, 3, 11, 0.8, 'Sama seperti material kain lain, hindari air panas'),
(5, 4, 10, 0.5, 'Tinta sulit lepas dari rajutan halus'),
(5, 5,  1, 0.7, 'Cuci menyeluruh karena jamur dapat menyebar di sela rajutan'),
(5, 6,  1, 0.8, 'Material mesh cukup tahan dicuci basah'),
(5, 7, 10, 0.4, 'Cat yang menempel pada rajutan sangat sulit diangkat sempurna'),
(5, 8,  1, 0.6, 'Cukup jarang terjadi pada mesh'),
(5, 9,  7, 0.9, 'Perawatan ringan, cukup dilap'),

-- === RUBBER / KARET (SOL) ===
(6, 1,  1, 0.8, 'Material tahan air dan sabun, mudah dibersihkan'),
(6, 2,  6, 0.8, 'Sikat setelah lumpur kering, sisa dilap basah'),
(6, 3, 11, 0.7, 'Hindari air panas agar darah tidak mengikat'),
(6, 4, 10, 0.7, 'Karet lebih tahan solvent dibanding material lain'),
(6, 5,  1, 0.8, 'Sikat dengan sabun antijamur, karet tahan gosokan'),
(6, 6,  1, 0.9, 'Paling mudah dibersihkan di antara semua material'),
(6, 7, 10, 0.7, 'Solvent cukup efektif mengangkat cat dari permukaan karet'),
(6, 8,  1, 0.6, 'Gosok dengan sikat, karat permukaan biasanya terangkat'),
(6, 9,  7, 0.9, 'Perawatan ringan rutin'),

-- === NUBUCK ===
(7, 1,  9, 0.6, 'Serupa suede, gunakan penyerap minyak sebelum dibersihkan'),
(7, 2,  6, 0.8, 'Tunggu kering lalu sikat searah serat'),
(7, 3,  9, 0.5, 'Material sensitif terhadap air berlebih'),
(7, 4,  3, 0.3, 'Risiko tinggi merusak tekstur, sebaiknya ke profesional'),
(7, 5,  9, 0.5, 'Gunakan cairan anti jamur khusus material berbulu'),
(7, 6,  5, 0.6, 'Tepuk dengan kain kering dahulu'),
(7, 7,  3, 0.3, 'Sangat berisiko, rujuk ke profesional'),
(7, 8,  9, 0.4, 'Jarang terjadi, perlu kehati-hatian'),
(7, 9,  6, 0.9, 'Perawatan rutin paling aman'),

-- === SATIN ===
(8, 1,  3, 0.6, 'Material halus dan mudah rusak bila digosok langsung'),
(8, 2,  5, 0.6, 'Bersihkan perlahan tanpa digosok kasar'),
(8, 3, 11, 0.5, 'Hasil bervariasi tergantung jenis serat satin'),
(8, 4,  3, 0.3, 'Sangat berisiko, disarankan ke jasa profesional'),
(8, 5,  3, 0.4, 'Material tipis rentan rusak oleh cairan kimia'),
(8, 6,  5, 0.6, 'Tangani cepat sebelum noda menyerap serat halus'),
(8, 7,  3, 0.3, 'Risiko tinggi, sebaiknya dirujuk ke profesional'),
(8, 8,  5, 0.4, 'Jarang terjadi pada material satin'),
(8, 9,  7, 0.9, 'Perawatan ringan rutin, cukup dilap lembut');
