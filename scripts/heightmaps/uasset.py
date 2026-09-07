"""Lector minimo de paquetes UE5 'legacy' — los que escribe `retoc to-legacy`.

No pretende ser un parser completo de Unreal: lee lo justo para sacar el Landscape
de S.T.A.L.K.E.R. 2 (mapa de nombres, tabla de exports, propiedades etiquetadas).

Por que a mano y no CUE4Parse: CUE4Parse es .NET y en esta maquina no hay dotnet
(verificado 2026-09-05). El formato que escribe retoc es una sola variante, no las
treinta que soporta CUE4Parse, asi que el subconjunto alcanza.
"""
import struct


class Reader:
    def __init__(self, data, pos=0):
        self.d = data
        self.p = pos

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v

    def i32(self):
        v = struct.unpack_from("<i", self.d, self.p)[0]; self.p += 4; return v

    def u32(self):
        v = struct.unpack_from("<I", self.d, self.p)[0]; self.p += 4; return v

    def i64(self):
        v = struct.unpack_from("<q", self.d, self.p)[0]; self.p += 8; return v

    def f32(self):
        v = struct.unpack_from("<f", self.d, self.p)[0]; self.p += 4; return v

    def f64(self):
        v = struct.unpack_from("<d", self.d, self.p)[0]; self.p += 8; return v

    def string(self):
        """FString: longitud con signo. Negativa = UTF-16. Incluye el NUL final."""
        n = self.i32()
        if n == 0:
            return ""
        if n < 0:
            raw = self.d[self.p:self.p - 2 * n]; self.p += -2 * n
            return raw.decode("utf-16-le").rstrip("\0")
        raw = self.d[self.p:self.p + n]; self.p += n
        return raw.decode("utf-8", "replace").rstrip("\0")


class Package:
    """Un .umap/.uasset legacy con su .uexp al lado."""

    def __init__(self, path_noext):
        self.base = path_noext
        with open(path_noext + self.header_ext(), "rb") as f:
            self.hdr = f.read()
        self.names = []
        self._read_summary()
        self._read_names()

    def header_ext(self):
        import os
        return ".umap" if os.path.exists(self.base + ".umap") else ".uasset"

    def _read_summary(self):
        r = Reader(self.hdr)
        tag = r.u32()
        if tag != 0x9E2A83C1:
            raise ValueError(f"tag inesperado 0x{tag:08X}")
        self.legacy_version = r.i32()          # -8 en lo que escribe retoc
        r.i32()                                # LegacyUE3Version
        self.ue4_version = r.i32()
        self.ue5_version = r.i32()
        r.i32()                                # FileVersionLicenseeUE4
        ncustom = r.i32()
        r.p += ncustom * 20                    # FCustomVersion = FGuid + int32
        self.total_header_size = r.i32()
        self.folder_name = r.string()
        self.package_flags = r.u32()
        self.name_count = r.i32()
        self.name_offset = r.i32()
        # De aca en adelante los campos son condicionales por version y retoc
        # escribe ceros en las versiones, asi que no se pueden usar para decidir.
        # Los offsets que faltan se localizan por deteccion (ver _find_tables).
        self._rest = r.p

    def _read_names(self):
        r = Reader(self.hdr, self.name_offset)
        for _ in range(self.name_count):
            s = r.string()
            r.p += 4                           # hashes (u16 casePreserving + u16)
            self.names.append(s)

    def name(self, idx):
        return self.names[idx] if 0 <= idx < len(self.names) else f"<name {idx}>"


# --- Tablas de imports y exports -------------------------------------------
#
# Los offsets de estas tablas viven en campos del summary que son condicionales
# por version de motor, y retoc escribe 0 en las versiones — asi que no se puede
# decidir por version. Se leen por posicion fija, pero RELATIVA al final de
# NameOffset: antes viene el nombre del paquete como FString, y su largo cambia
# con el nombre de la celda (`X0Y0` contra `X-1Y-1`). Con offsets absolutos
# andaban 59 celdas de 241 y las demas reventaban.
_REL_EXPORT_COUNT = 16
_REL_EXPORT_OFFSET = 20
_REL_IMPORT_COUNT = 24
_REL_IMPORT_OFFSET = 28
_REL_DEPENDS_OFFSET = 32

EXPORT_ENTRY_SIZE = 96   # verificado: (DependsOffset - ExportOffset) / ExportCount
IMPORT_ENTRY_SIZE = 32   # verificado: (ExportOffset - ImportOffset) / ImportCount


class Export:
    __slots__ = ("index", "class_index", "outer_index", "name", "name_number",
                 "serial_size", "serial_offset")

    def __repr__(self):
        n = self.name + (f"_{self.name_number - 1}" if self.name_number else "")
        return f"<Export {self.index} {n} size={self.serial_size}>"

    @property
    def full_name(self):
        return self.name + (f"_{self.name_number - 1}" if self.name_number else "")


class Import:
    __slots__ = ("index", "class_package", "class_name", "outer_index", "name")

    def __repr__(self):
        return f"<Import {self.index} {self.class_name}'{self.name}'>"


def _fname(pkg, r):
    idx = r.i32()
    num = r.i32()
    return pkg.name(idx), num


def _load_tables(self):
    d = self.hdr
    b = self._rest
    self.export_count = struct.unpack_from("<i", d, b + _REL_EXPORT_COUNT)[0]
    self.export_offset = struct.unpack_from("<i", d, b + _REL_EXPORT_OFFSET)[0]
    self.import_count = struct.unpack_from("<i", d, b + _REL_IMPORT_COUNT)[0]
    self.import_offset = struct.unpack_from("<i", d, b + _REL_IMPORT_OFFSET)[0]
    self.depends_offset = struct.unpack_from("<i", d, b + _REL_DEPENDS_OFFSET)[0]

    got = (self.depends_offset - self.export_offset) // max(self.export_count, 1)
    if got != EXPORT_ENTRY_SIZE:
        raise ValueError(f"export entry de {got} bytes, esperaba {EXPORT_ENTRY_SIZE}")

    self.imports = []
    r = Reader(d, self.import_offset)
    for i in range(self.import_count):
        im = Import()
        im.index = i
        im.class_package, _ = _fname(self, r)
        im.class_name, _ = _fname(self, r)
        im.outer_index = r.i32()
        im.name, _ = _fname(self, r)
        r.i32()                            # bImportOptional
        self.imports.append(im)

    self.exports = []
    for i in range(self.export_count):
        base = self.export_offset + i * EXPORT_ENTRY_SIZE
        r = Reader(d, base)
        e = Export()
        e.index = i
        e.class_index = r.i32()
        r.i32()                                # SuperIndex
        r.i32()                                # TemplateIndex
        e.outer_index = r.i32()
        e.name, e.name_number = _fname(self, r)
        r.u32()                                # ObjectFlags
        e.serial_size = r.i64()
        e.serial_offset = r.i64()
        self.exports.append(e)


def _class_of(self, e):
    """Nombre de la clase de un export. class_index es un FPackageIndex:
    positivo = export (1-based), negativo = import (1-based), 0 = None."""
    ci = e.class_index
    if ci < 0:
        return self.imports[-ci - 1].name
    if ci > 0:
        return self.exports[ci - 1].full_name
    return "None"


Package.load_tables = _load_tables
Package.class_of = _class_of
