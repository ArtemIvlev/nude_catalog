WITH RankedPhotos AS (
  SELECT *,
         ROW_NUMBER() OVER (PARTITION BY hash_sha256 ORDER BY id) AS rn
  FROM photos_ok
  WHERE is_nude = 1
    AND has_face = 0
    AND is_small = 0
    AND status = "approved"
)
SELECT *
FROM RankedPhotos
WHERE rn = 1;
