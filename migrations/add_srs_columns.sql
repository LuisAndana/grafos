-- ═══════════════════════════════════════════════════════════════════════
-- Migración: Agregar TODAS las columnas faltantes a srs_documentos
-- La tabla actual solo tiene: id_srs, proyecto_id, generado_por,
-- introduccion, fecha_generacion, created_at, updated_at
-- ═══════════════════════════════════════════════════════════════════════

ALTER TABLE srs_documentos
    ADD COLUMN nombre_documento              VARCHAR(255) NOT NULL DEFAULT 'SRS' AFTER proyecto_id,
    ADD COLUMN stakeholders                  JSON NULL DEFAULT NULL AFTER introduccion,
    ADD COLUMN usuarios                      JSON NULL DEFAULT NULL AFTER stakeholders,
    ADD COLUMN requerimientos_funcionales    JSON NULL DEFAULT NULL AFTER usuarios,
    ADD COLUMN requerimientos_no_funcionales JSON NULL DEFAULT NULL AFTER requerimientos_funcionales,
    ADD COLUMN casos_uso                     JSON NULL DEFAULT NULL AFTER requerimientos_no_funcionales,
    ADD COLUMN restricciones                 JSON NULL DEFAULT NULL AFTER casos_uso,
    ADD COLUMN elicitacion                   JSON NULL DEFAULT NULL AFTER restricciones,
    ADD COLUMN negociaciones                 JSON NULL DEFAULT NULL AFTER elicitacion,
    ADD COLUMN validacion_info               JSON NULL DEFAULT NULL AFTER negociaciones,
    ADD COLUMN artefactos_info               JSON NULL DEFAULT NULL AFTER validacion_info,
    ADD COLUMN estado                        VARCHAR(50) NOT NULL DEFAULT 'Borrador' AFTER artefactos_info,
    ADD COLUMN version                       VARCHAR(20) NOT NULL DEFAULT '1.0' AFTER estado;
