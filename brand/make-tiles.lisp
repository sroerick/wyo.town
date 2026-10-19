;;;; wyo.town asset generator
;;;; Pixel-art tiles and palette specimens, drawn as flat rectangles.
;;;; Everything is emitted as SVG with shape-rendering: crispEdges, so every
;;;; shape stays a hard-edged pixel at any display size.
;;;;
;;;; Patterns are drawn on a 16 by 16 grid. Anything that represents an object
;;;; is drawn on 32 by 32, because at 16 the figures were too coarse to read
;;;; as the things they were meant to be. The hourglass is emitted as an
;;;; eight-frame animation; everything else is a single still frame.

(defpackage :wyo-assets
  (:use :cl)
  (:export :build-all))

(in-package :wyo-assets)

(defparameter *dir* (merge-pathnames "assets/" (or *load-truename* #p"./")))  ; run me from anywhere
(defparameter *pixel* 8)

;;; ------------------------------------------------------------------ grids

(defun blank-grid (w h fill)
  "A fresh vector of H strings, each W chars of FILL."
  (let ((g (make-array h)))
    (dotimes (y h) (setf (aref g y) (make-string w :initial-element fill)))
    g))

(defun grid-from-rows (rows)
  (let ((w (length (first rows))))
    (dolist (r rows)
      (unless (= (length r) w)
        (error "ragged tile row: ~S has ~D chars, expected ~D" r (length r) w)))
    (coerce (mapcar #'copy-seq rows) 'vector)))

(defun px (g x y) (char (aref g y) x))
(defun (setf px) (v g x y) (setf (char (aref g y) x) v))

;;; ------------------------------------------------------- runs to rectangles

(defun row-runs (row color)
  "((start length) ...) for COLOR in ROW."
  (let ((n (length row)) (out '()) (x 0))
    (loop while (< x n) do
      (if (char= (char row x) color)
          (let ((start x))
            (loop while (and (< x n) (char= (char row x) color)) do (incf x))
            (push (list start (- x start)) out))
          (incf x)))
    (nreverse out)))

(defun color-runs (frames color)
  "((x y w) ...) for COLOR across FRAMES, laid out left to right."
  (let ((w (length (aref (first frames) 0))))
    (loop for frame in frames
          for fi from 0
          append (loop for y from 0 below (length frame)
                       append (loop for (start len) in (row-runs (aref frame y) color)
                                    collect (list (+ (* fi w) start) y len))))))

(defun merge-vertical (runs)
  "Collapse (x y w) runs that stack into taller blocks -> (x y w h)."
  (let ((groups (make-hash-table :test 'equal)) (out '()))
    (dolist (r runs) (push r (gethash (list (first r) (third r)) groups)))
    (maphash
     (lambda (key ys)
       (declare (ignore key))
       (let* ((x (first (first ys)))
              (w (third (first ys)))
              (sorted (sort (copy-list ys) #'< :key #'second))
              (start (second (first sorted)))
              (prev start))
         (dolist (r (rest sorted))
           (if (= (second r) (1+ prev))
               (setf prev (second r))
               (progn (push (list x start w (1+ (- prev start))) out)
                      (setf start (second r) prev (second r)))))
         (push (list x start w (1+ (- prev start))) out)))
     groups)
    (nreverse out)))

(defun rects->path (rects)
  (with-output-to-string (s)
    (dolist (r rects)
      (destructuring-bind (x y w h) r
        (format s "M~D ~Dh~Dv~Dh-~Dz" x y w h w)))))

;;; ----------------------------------------------------------------- output

(defun write-svg-head (s w h pixel title)
  (format s "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 ~D ~D\" width=\"~D\" height=\"~D\" preserveAspectRatio=\"none\" shape-rendering=\"crispEdges\">~%"
          w h (* w pixel) (* h pixel))
  (when title (format s "  <title>~A</title>~%" title)))

(defun write-frame-shapes (s frame palette)
  (loop for (char . hex) in (rest palette)
        for rects = (merge-vertical (color-runs (list frame) char))
        when rects do
          (format s "  <path fill=\"~A\" d=\"~A\"/>~%" hex (rects->path rects))))

(defun emit-svg (name frames palette &key (pixel *pixel*) title)
  "Write NAME.svg from FRAMES, an alist PALETTE of (char . hex).
   The first palette entry paints the background."
  (let* ((h (length (first frames)))
         (w (length (aref (first frames) 0)))
         (nf (length frames))
         (tw (* w nf))
         (path (merge-pathnames (format nil "~A.svg" name) *dir*)))
    (ensure-directories-exist path)
    (with-open-file (s path :direction :output :if-exists :supersede
                            :if-does-not-exist :create)
      (write-svg-head s tw h pixel title)
      (unless (string= (cdr (first palette)) "none")
        (format s "  <rect width=\"~D\" height=\"~D\" fill=\"~A\"/>~%"
                tw h (cdr (first palette))))
      (loop for (char . hex) in (rest palette)
            for rects = (merge-vertical (color-runs frames char))
            when rects do
              (format s "  <path fill=\"~A\" d=\"~A\"/>~%" hex (rects->path rects)))
      (format s "</svg>~%"))
    path))

(defun emit-anim-svg (name frames palette &key (pixel *pixel*) title (dur 1.6))
  "Write NAME.svg as a stepped animation: every frame occupies the same cell,
   and a discrete opacity animation cycles through them with no tweening."
  (let* ((h (length (first frames)))
         (w (length (aref (first frames) 0)))
         (nf (length frames))
         (path (merge-pathnames (format nil "~A.svg" name) *dir*)))
    (ensure-directories-exist path)
    (with-open-file (s path :direction :output :if-exists :supersede
                            :if-does-not-exist :create)
      (write-svg-head s w h pixel title)
      (unless (string= (cdr (first palette)) "none")
        (format s "  <rect width=\"~D\" height=\"~D\" fill=\"~A\"/>~%"
                w h (cdr (first palette))))
      (loop for frame in frames
            for i from 0
            do (format s "  <g>~%")
               (format s "    <animate attributeName=\"opacity\" calcMode=\"discrete\" values=\"~{~D~^;~}\" dur=\"~As\" repeatCount=\"indefinite\"/>~%"
                       (loop for j below nf collect (if (= j i) 1 0)) dur)
               (write-frame-shapes s frame palette)
               (format s "  </g>~%"))
      (format s "</svg>~%"))
    path))

(defun emit-swatches (name colors cols cell &key (pixel 1) title)
  "Write NAME.svg as a grid of flat colour cells, COLORS wide by however many rows."
  (let* ((n (length colors))
         (rows (ceiling n cols))
         (w (* cols cell))
         (h (* rows cell))
         (path (merge-pathnames (format nil "~A.svg" name) *dir*)))
    (ensure-directories-exist path)
    (with-open-file (s path :direction :output :if-exists :supersede
                            :if-does-not-exist :create)
      (format s "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 ~D ~D\" width=\"~D\" height=\"~D\" preserveAspectRatio=\"none\" shape-rendering=\"crispEdges\">~%"
              w h (* w pixel) (* h pixel))
      (when title (format s "  <title>~A</title>~%" title))
      (loop for c in colors
            for i from 0
            for x = (* cell (mod i cols))
            for y = (* cell (floor i cols))
            do (format s "  <rect x=\"~D\" y=\"~D\" width=\"~D\" height=\"~D\" fill=\"~A\"/>~%"
                       x y cell cell c))
      (format s "</svg>~%"))
    path))

;;; --------------------------------------------------- shape primitives

(defun blob-fill (g cx cy rx ry ch)
  "Fill an ellipse into G."
  (dotimes (y (length g))
    (dotimes (x (length (aref g 0)))
      (let ((dx (/ (- x cx) rx)) (dy (/ (- y cy) ry)))
        (when (<= (+ (* dx dx) (* dy dy)) 1.0)
          (setf (px g x y) ch))))))

(defun outline-color (g ch edge)
  "Every CH cell touching a cell that is neither CH nor EDGE becomes EDGE."
  (let* ((h (length g)) (w (length (aref g 0)))
         (copy (map 'vector #'copy-seq g)))
    (dotimes (y h)
      (dotimes (x w)
        (when (char= (px copy x y) ch)
          (dolist (d '((-1 0) (1 0) (0 -1) (0 1) (-1 -1) (1 -1) (-1 1) (1 1)))
            (let ((nx (+ x (first d))) (ny (+ y (second d))))
              (when (and (< -1 nx w) (< -1 ny h))
                (let ((c (px copy nx ny)))
                  (unless (or (char= c ch) (char= c edge))
                    (setf (px g x y) edge)))))))))
    g))

(defun in-circle (x y cx cy r)
  (<= (+ (* (- x cx) (- x cx)) (* (- y cy) (- y cy))) (* r r)))

(defun roughen (g ch seed &key (prob 34))
  "Nibble the boundary between CH and its surroundings, seeded, so a filled
   blob stops reading as a circle."
  (let* ((h (length g)) (w (length (aref g 0))) (state seed)
         (copy (map 'vector #'copy-seq g)))
    (flet ((next (n)
             (setf state (mod (+ (* state 1103515245) 12345) 2147483648))
             (mod (floor state 65536) n)))
      (dotimes (y h)
        (dotimes (x w)
          (unless (char= (px copy x y) ch)
            (let ((touch nil))
              (dolist (d '((-1 0) (1 0) (0 -1) (0 1)))
                (let ((nx (+ x (first d))) (ny (+ y (second d))))
                  (when (and (< -1 nx w) (< -1 ny h) (char= (px copy nx ny) ch))
                    (setf touch t))))
              (when (and touch (< (next 100) prob))
                (setf (px g x y) ch)))))))
    g))

;;; ----------------------------------------------------- pattern generators

(defun dither-grid (w h a b)
  (let ((g (blank-grid w h a)))
    (dotimes (y h) (dotimes (x w)
      (setf (px g x y) (if (evenp (+ x y)) a b))))
    g))

(defun hazard-grid (w h a b period)
  (let ((g (blank-grid w h a)))
    (dotimes (y h) (dotimes (x w)
      (setf (px g x y) (if (< (mod (+ x y) period) (floor period 2)) a b))))
    g))

(defun ripple-grid (w h bg deep)
  (let ((g (blank-grid w h bg)))
    (loop for x below w
          for y0 = (round (+ (/ h 2) (* 4 (sin (* 2 pi (/ x w))))))
          do (loop for y from (max 0 (1- y0)) to (min (1- h) (1+ y0))
                   do (setf (px g x y) deep)))
    g))

(defun granite-grid (w h base light dark fleck &key (seed 20261017))
  (let ((state seed))
    (flet ((next (n)
             (setf state (mod (+ (* state 1103515245) 12345) 2147483648))
             (mod (floor state 65536) n)))
      (coerce
       (loop for y below h
             collect (coerce
                      (loop for x below w
                            for r = (next 100)
                            collect (cond ((< r 8) fleck)
                                          ((< r 30) light)
                                          ((< r 52) dark)
                                          (t base)))
                      'string))
       'vector))))

(defun graph-grid (w h field line step)
  "Graph paper: a flat field ruled with LINE every STEP cells."
  (let ((g (blank-grid w h field)))
    (loop for y from 0 below h by step do
      (loop for x below w do (setf (px g x y) line)))
    (loop for x from 0 below w by step do
      (loop for y below h do (setf (px g x y) line)))
    g))

(defun cowhide-grid (w h hide field &key (seed 991))
  "Overlapping irregular patches, roughened at the edge so they read as hide
   rather than as circles. Painted with wrap-around so the tile repeats."
  (let ((g (blank-grid w h field)))
    (dolist (patch '((7 7 4) (25 6 4) (17 13 4) (5 19 3) (30 15 3)
                     (26 25 5) (10 27 3) (22 8 2) (13 4 2) (2 29 3)
                     (31 30 3) (20 20 2)))
      (destructuring-bind (cx cy r) patch
        (dotimes (y h) (dotimes (x w)
          (let* ((ax (abs (- x cx))) (ay (abs (- y cy)))
                 (dx (min ax (- w ax))) (dy (min ay (- h ay))))
            (when (<= (+ (* dx dx) (* dy dy)) (* r r))
              (setf (px g x y) hide)))))))
    (roughen g hide seed :prob 42)
    g))

;;; ------------------------------------------------------- object generators

(defun bullet-grid (w h ball light dark edge)
  "A beveled ball, the list marker of the period. A figure, so it sits on any
   field."
  (let* ((g (blank-grid w h #\.))
         (c (/ (1- w) 2.0))
         (r (* w 0.42))
         (inner (- r 1)))
    (dotimes (y h) (dotimes (x w)
      (let* ((dx (- x c)) (dy (- y c))
             (d (sqrt (+ (* dx dx) (* dy dy)))))
        (when (<= d r)
          (setf (px g x y)
                (cond ((> d inner) edge)
                      ((and (< (+ dx dy) (* -0.35 r))
                            (< (+ (* dx dx) (* dy dy)) (* 0.72 r 0.72 r))) light)
                      ((> (+ dx dy) (* 0.45 r)) dark)
                      (t ball)))))))
    g))

(defun hourglass-frames (w h)
  "Eight frames of a draining hourglass. The sand runs from the top chamber to
   the bottom with a grain falling through the neck."
  (let* ((cx (/ w 2.0))
         (top-y 3) (mid-y (floor (/ h 2))) (bot-y (- h 4))
         (half-top (max 2 (floor (- w 8) 2)))
         (nf 8)
         (frames '()))
    (flet ((hw (y)
             (let* ((d (if (<= y mid-y) (- mid-y y) (- y mid-y)))
                    (dd (if (<= y mid-y) (- mid-y top-y) (- bot-y mid-y))))
               (max 1 (round (* half-top (/ d (float dd))))))))
      (dotimes (i nf)
        (let* ((f (/ (float i) (1- nf)))       ; 0 full, 1 drained
               (g (blank-grid w h #\.)))
          ;; caps
          (loop for x from 2 to (- w 3)
                do (setf (px g x 1) #\k) (setf (px g x 2) #\k)
                   (setf (px g x (- h 2)) #\k) (setf (px g x (- h 3)) #\k))
          ;; glass walls and interior
          (loop for y from top-y to bot-y
                for hh = (hw y)
                do (loop for x from (- (round cx) hh) to (+ (round cx) hh)
                         do (setf (px g x y) #\g))
                   (setf (px g (- (round cx) hh 1) y) #\k)
                   (setf (px g (+ (round cx) hh 1) y) #\k))
          ;; sand
          (let ((top-rows (round (* (- 1 f) (- mid-y top-y 1))))
                (bot-rows (round (* f (- bot-y mid-y 1)))))
            (loop for y from top-y below (+ top-y top-rows)
                  for hh = (hw y)
                  do (loop for x from (- (round cx) hh) to (+ (round cx) hh)
                           do (setf (px g x y) #\a)))
            (loop for y from (- bot-y bot-rows) to bot-y
                  for hh = (hw y)
                  do (loop for x from (- (round cx) hh) to (+ (round cx) hh)
                           do (setf (px g x y) #\a)))
            (when (and (> f 0) (< f 1))
              (loop for y from (1+ top-y) to (1- bot-y)
                    do (setf (px g (round cx) y) #\a))))
          (push g frames))))
    (nreverse frames)))

(defun sunset-grid (w h sky mid sun)
  "The retro sun: a disc in three flat bands, sliced by horizontal cuts, the
   way the period drew a setting sun. A figure, transparent behind."
  (let* ((g (blank-grid w h #\.))
         (cx (/ w 2.0))
         (cy (+ (/ h 2.0) 1.0))
         (r (* w 0.4)))
    (dotimes (y h) (dotimes (x w)
      (let ((d (+ (* (- x cx) (- x cx)) (* (- y cy) (- y cy)))))
        (when (<= d (* r r))
          (if (and (>= y (+ cy 2)) (zerop (mod (- y (floor (+ cy 2))) 3)))
              (setf (px g x y) #\.)                 ; the cut
              (setf (px g x y)
                    (cond ((< y (- cy (* 0.2 r))) sky)
                          ((< y (+ cy (* 0.35 r))) mid)
                          (t sun))))))))
    g))

(defun pricklypear-grid (w h pad edge spine bloom)
  "Three pads and a bloom: the cactus that grows where the map says nothing
   should."
  (let ((g (blank-grid w h #\.)))
    (blob-fill g 16.0 21.5 8.6 9.0 pad)
    (blob-fill g 7.5 11.5 5.4 6.2 pad)
    (blob-fill g 24.0 11.0 5.2 6.0 pad)
    (blob-fill g 15.0 9.0 1.8 3.2 pad)
    (outline-color g pad edge)
    (let ((state 5))
      (flet ((next (n)
               (setf state (mod (+ (* state 1103515245) 12345) 2147483648))
               (mod (floor state 65536) n)))
        (dotimes (y h) (dotimes (x w)
          (when (and (char= (px g x y) pad) (zerop (next 6)))
            (setf (px g x y) spine))))))
    (blob-fill g 24.0 3.6 2.3 2.4 bloom)
    g))

(defun sage-grid (w h leaf alt shade stem)
  "A low silver mound on a short woody stem: the shrub that grows where nothing
   else will."
  (let ((g (blank-grid w h #\.)))
    (blob-fill g 16.0 16.5 10.0 8.0 leaf)
    (blob-fill g 9.0 13.5 6.0 5.0 leaf)
    (blob-fill g 23.0 13.5 6.0 5.0 leaf)
    (blob-fill g 12.0 9.0 4.6 4.0 leaf)
    (blob-fill g 20.0 9.0 4.6 4.0 leaf)
    (blob-fill g 16.0 8.0 5.2 4.0 leaf)
    (let ((state 11))
      (flet ((next (n)
               (setf state (mod (+ (* state 1103515245) 12345) 2147483648))
               (mod (floor state 65536) n)))
        (dotimes (y h) (dotimes (x w)
          (when (char= (px g x y) leaf)
            (let ((r (next 100)))
              (cond ((< r 18) (setf (px g x y) alt))
                    ((< r 30) (setf (px g x y) shade)))))))))
    (loop for y from 23 to 29
          do (setf (px g 15 y) stem) (setf (px g 16 y) stem))
    g))

(defun mountain-grid (w h rock snow)
  "One bold peak with a dithered snowline."
  (let ((g (blank-grid w h #\.)))
    (loop for y from 3 to 12
          for half = (round (* 8 (/ (- y 3) 9.0)))
          do (loop for x from (- 7 half) to (+ 8 half)
                   do (when (and (< -1 x w)) (setf (px g x y) rock))))
      (loop for y from 3 to 6
            do (loop for x from 0 to (1- w)
                     do (when (char= (px g x y) rock) (setf (px g x y) snow))))
      (loop for x from 0 to (1- w)
            do (when (and (char= (px g x 7) rock) (evenp x))
                 (setf (px g x 7) snow)))
    g))

(defun starburst-grid (w h ch)
  "A four point sparkle with concave edges: the badge the period could not
   stop drawing."
  (let* ((g (blank-grid w h #\.))
         (c (/ (1- w) 2.0))
         (reach (* w 0.5))
         (limit (sqrt reach)))
    (dotimes (y h) (dotimes (x w)
      (let ((dx (- x c)) (dy (- y c)))
        (when (<= (+ (sqrt (abs dx)) (sqrt (abs dy))) limit)
          (setf (px g x y) ch)))))
    g))

(defun disc-grid (w h metal shine ring hub)
  "The medium: a compact disc, caught on the one angle that looked like a
   rainbow."
  (let ((g (blank-grid w h #\.)) (c 7.5))
    (dotimes (y h)
      (dotimes (x w)
        (when (in-circle x y c c 7.2) (setf (px g x y) metal))))
    (dotimes (y h)
      (dotimes (x w)
        (when (in-circle x y c c 7.2)
          (let ((d (sqrt (+ (* (- x c) (- x c)) (* (- y c) (- y c))))))
            (cond ((< d 1.6) (setf (px g x y) hub))
                  ((< d 2.7) (setf (px g x y) ring))
                  ((and (< 2.7 d 7.2) (< x c) (< y c)) (setf (px g x y) shine)))))))
    g))

(defun moon-grid (w h moon star)
  "A crescent and three sparks."
  (let ((g (blank-grid w h #\.)))
    (dotimes (y h)
      (dotimes (x w)
        (when (and (in-circle x y 17.0 16.5 12.5)
                   (not (in-circle x y 23.0 12.0 11.0)))
          (setf (px g x y) moon))))
    (dolist (p '((6 6 4) (26 7 3) (7 26 3)))
      (destructuring-bind (cx cy s) p
        (dotimes (y h) (dotimes (x w)
          (when (and (<= (abs (- x cx)) s) (<= (abs (- y cy)) s)
                     (or (= x cx) (= y cy)))
            (setf (px g x y) star))))))
    g))

(defun trout-grid (w h back side slash spot)
  "A Yellowstone cutthroat, facing left: the fish the streams were made for."
  (let ((g (blank-grid w h #\.))
        (state 23))
    (flet ((next (n)
             (setf state (mod (+ (* state 1103515245) 12345) 2147483648))
             (mod (floor state 65536) n))
           (inbody (x y)
             (<= (+ (expt (/ (- x 15.0) 11.0) 2)
                    (expt (/ (- y 15.0) 5.5) 2))
                 1.0))
           (intail (x y)
             (and (<= 26 x 30)
                  (let* ((th (max 0.0 (float (- x 24.5))))
                         (d (abs (- y 15.5))))
                    (and (<= d th) (> d (max 0.5 (* 0.35 th)))))))
           (infin (x y)
             (or (and (<= 12 x 18) (<= (+ 6.5 (* 0.8 (abs (- x 15)))) y 10.0)) ; dorsal
                 (and (<= 12 x 14) (<= 20.5 y (+ 20.5 (* 0.9 (- x 11)))))     ; pectoral
                 (and (<= 3 x 4) (<= 14 y 15)))))                              ; mouth
      ;; paint
      (dotimes (y h)
        (dotimes (x w)
          (cond ((or (intail x y) (infin x y)) (setf (px g x y) back))
                ((inbody x y)
                 (setf (px g x y) (if (<= y 12) back side))
                 (when (and (<= 8 x 10) (<= 18 y 19)) (setf (px g x y) slash))
                 (when (and (<= 11 y 15) (<= 8 x 24) (< (next 100) 16))
                   (setf (px g x y) spot))))))
      ;; join tail to body, then the eye
      (setf (px g 26 15) back) (setf (px g 26 16) back)
      (setf (px g 7 14) spot)
      ;; ink silhouette: every painted cell touching transparency
      (let ((copy (map 'vector #'copy-seq g)))
        (dotimes (y h)
          (dotimes (x w)
            (when (and (not (char= (px copy x y) #\.))
                       (some (lambda (d)
                               (let ((nx (+ x (first d)))
                                     (ny (+ y (second d))))
                                 (or (< nx 0) (>= nx w) (< ny 0) (>= ny h)
                                     (char= (px copy nx ny) #\.))))
                             '((1 0) (-1 0) (0 1) (0 -1))))
              (setf (px g x y) #\e))))))
      g))

(defun stream-grid (w h sand deep water glint)
  "A stream seen from above: sand banks, a cutting current, sky glints."
  (let ((g (blank-grid w h #\.)))
    (dotimes (y h)
      (let ((cx (+ 15.5 (* 6.5 (sin (* 2 pi 1.2 (/ y (float h))))))))
        (dotimes (x w)
          (let ((dd (abs (- x cx))))
            (cond ((<= dd 3.2)
                   (setf (px g x y) (if (zerop (mod (+ (* 3 x) y) 13)) glint water)))
                  ((<= dd 4.2) (setf (px g x y) deep))
                  ((<= dd 6.2) (setf (px g x y) sand)))))))
    g))

(defun cottonwood-grid (w h gold shade leaf trunk)
  "A plains cottonwood in October: the tree that marks water in the desert."
  (let ((g (blank-grid w h #\.)))
    (blob-fill g 16.0 11.0 10.0 8.0 gold)
    (blob-fill g 10.0 13.0  6.0 5.0 gold)
    (blob-fill g 22.0 13.0  6.0 5.0 gold)
    (blob-fill g 16.0  6.0  5.0 4.0 gold)
    (roughen g gold 77 :prob 22)
    ;; shade, low right
    (dotimes (y h) (dotimes (x w)
      (when (and (char= (px g x y) gold) (> (+ x y) 27))
        (setf (px g x y) shade))))
    ;; light through the leaves
    (let ((state 13))
      (flet ((next (n)
               (setf state (mod (+ (* state 1103515245) 12345) 2147483648))
               (mod (floor state 65536) n)))
        (dotimes (y h) (dotimes (x w)
          (when (and (char= (px g x y) gold) (< (next 100) 8))
            (setf (px g x y) leaf))))))
    ;; trunk and two branches
    (loop for y from 19 to 31
          do (setf (px g 15 y) trunk) (setf (px g 16 y) trunk))
    (dotimes (i 3)
      (setf (px g (+ 12 i) (- 20 i)) trunk)
      (setf (px g (- 19 i) (- 19 i)) trunk))
    g))

;;; ------------------------------------------------------------------ build

(defun build-all ()
  (let ((made '()))
    (flet ((out (name &rest args)
             (ensure-directories-exist (merge-pathnames "x" *dir*))
             (push (apply #'emit-svg name args) made)))

      ;; 01 the cloud tile: the archetype of the era
      (out "tile-cloud"
           (list (grid-from-rows
                  '("................"
                    "................"
                    "................"
                    ".....wwww......."
                    "...wwwwwwww....."
                    "..wwwwwwwwwww..."
                    ".wwwwwwwwwwwwww."
                    ".wwwwwwwwwwwwww."
                    "..wwwwwwwwwwww.."
                    "...ssssssssss..."
                    "................"
                    "................"
                    "................"
                    "................"
                    "................"
                    "................")))
           '((#\. . "#88CCEE") (#\w . "#FFFFFF") (#\s . "#D2E9F5"))
           :title "cloud tile, 16x16")

      ;; 02 graph paper, where the starfield tile used to be
      (out "tile-grid"
           (list (graph-grid 16 16 #\f #\l 4))
           '((#\f . "#101418") (#\l . "#C8F24E"))
           :title "grid tile, 16x16")

      ;; 03 the 50 percent dither: how the era shaded anything
      (out "tile-dither"
           (list (dither-grid 16 16 #\a #\b))
           '((#\a . "#1E6BFF") (#\b . "#88CCEE"))
           :title "dither tile, 50 percent")

      ;; 04 hazard stripes, the under construction barricade (WITHDRAWN T-04)
      (out "tile-hazard"
           (list (hazard-grid 16 16 #\a #\b 8))
           '((#\a . "#FFB300") (#\b . "#101418"))
           :title "hazard tile, 45 degrees")

      ;; 05 water ripple
      (out "tile-ripple"
           (list (ripple-grid 16 16 #\l #\d))
           '((#\l . "#BCE8F0") (#\d . "#2E8FA8"))
           :title "ripple tile")

      ;; 06 granite
      (out "tile-granite"
           (list (granite-grid 16 16 #\m #\l #\d #\f))
           '((#\m . "#8E8E8A") (#\l . "#B8B8B2") (#\d . "#63635F") (#\f . "#EAEAE4"))
           :title "granite tile")

      ;; 07 the beveled ball, for lists (WITHDRAWN T-07)
      (out "tile-bullet"
           (list (bullet-grid 32 32 #\o #\l #\d #\e))
           '((#\. . "none") (#\e . "#101418") (#\o . "#FFB300")
             (#\l . "#FFE38A") (#\d . "#AA3311"))
           :title "bullet tile, 32x32")

      ;; 08 the hourglass, eight frames, animated
      (ensure-directories-exist (merge-pathnames "x" *dir*))
      (push (emit-anim-svg "tile-hourglass"
                           (hourglass-frames 32 32)
                           '((#\. . "#F6F5F0") (#\g . "#DAE2E8") (#\k . "#101418")
                             (#\a . "#FFB300"))
                           :dur 2.0
                           :title "hourglass, eight frames, animated")
            made)

      ;; 09 cowhide: Gateway 2000 bought cattle at auction, Wyoming registers brands
      (out "tile-cowhide"
           (list (cowhide-grid 32 32 #\s #\p))
           '((#\p . "#F6F5F0") (#\s . "#101418"))
           :title "cowhide tile, 32x32")

      ;; 10 the retro sun, sliced (WITHDRAWN T-10)
      (out "tile-sunset"
           (list (sunset-grid 32 32 #\a #\b #\c))
           '((#\. . "none") (#\a . "#FFB300") (#\b . "#FF7A45") (#\c . "#FF3EA5"))
           :title "sunset tile, 32x32")

      ;; 11 to 16: the figures
      (out "tile-pricklypear"
           (list (pricklypear-grid 32 32 #\p #\e #\s #\f))
           '((#\. . "none") (#\p . "#4E8C4A") (#\e . "#2C4A28")
             (#\s . "#E8F2D0") (#\f . "#FFB300"))
           :title "pricklypear tile, 32x32")

      (out "tile-sage"
           (list (sage-grid 32 32 #\l #\a #\s #\r))
           '((#\. . "none") (#\l . "#9AA894") (#\a . "#C2CFB8")
             (#\s . "#7C8A76") (#\r . "#6B5B4A"))
           :title "sage tile, 32x32")

      (out "tile-mountain"
           (list (mountain-grid 16 16 #\r #\s))
             '((#\. . "none") (#\r . "#2A3340") (#\s . "#FFFFFF"))
           :title "mountain tile")

      (out "tile-starburst"
           (list (starburst-grid 32 32 #\b))
             '((#\. . "none") (#\b . "#FFB300"))
           :title "starburst tile, 32x32")

      ;; 15 the compact disc (WITHDRAWN T-15)
      (out "tile-disc"
           (list (disc-grid 16 16 #\m #\h #\k #\k))
             '((#\. . "none") (#\m . "#C8CCD0") (#\h . "#7FE8FF") (#\k . "#101418"))
           :title "disc tile")

      (out "tile-moon"
           (list (moon-grid 32 32 #\o #\t))
             '((#\. . "none") (#\o . "#FFD24A") (#\t . "#FFFFFF"))
           :title "moon tile, 32x32")

      ;; 17 strata: the river-cut bands of a canyon wall (replaces T-04)
      (out "tile-strata"
           (list (grid-from-rows
                  '("ssssssssssssssss"
                    "ssssssssssssssss"
                    "ssssssssssssssss"
                    "uuuuuuuuuuuuuuuu"
                    "uuuuuuuuuuuuuuuu"
                    "uuuuuaauuuuuuuuu"
                    "aaaaaaaaaaaaaaaa"
                    "aaaaaaaaaaarraaa"
                    "rrrrrrrrrrrrrrrr"
                    "rrrrrrrrrrrrrrrr"
                    "rrrrrrrrrrrrrrrr"
                    "rrrrrrrrrrrrrrrr"
                    "rruuuuuuuuuuuuuu"
                    "uuuuuuuuuuuuuuuu"
                    "ssssssssssssssss"
                    "ssssssssssssssss")))
           '((#\s . "#EAD2A0") (#\u . "#FF7A45") (#\a . "#FFB300") (#\r . "#AA3311"))
           :title "strata tile, 16x16")

      ;; 18 a Yellowstone cutthroat (replaces T-07)
      (out "tile-trout"
           (list (trout-grid 32 32 #\b #\i #\h #\k))
           '((#\. . "none") (#\b . "#0B5D6B") (#\i . "#88CCEE")
             (#\h . "#FF7A45") (#\k . "#101418") (#\e . "#101418"))
           :title "trout tile, 32x32")

      ;; 19 a stream, from above (replaces T-10)
      (out "tile-stream"
           (list (stream-grid 32 32 #\s #\d #\w #\g))
           '((#\. . "none") (#\s . "#EAD2A0") (#\d . "#0B5D6B")
             (#\w . "#1E6BFF") (#\g . "#88CCEE"))
           :title "stream tile, 32x32")

      ;; 20 a cottonwood in October (replaces T-15)
      (out "tile-cottonwood"
           (list (cottonwood-grid 32 32 #\a #\s #\l #\k))
           '((#\. . "none") (#\a . "#FFB300") (#\s . "#FF7A45")
             (#\l . "#C8F24E") (#\k . "#101418"))
           :title "cottonwood tile, 32x32")

      ;; palette specimens
      (push (emit-swatches "palette-vga16"
                           '("#000000" "#0000AA" "#00AA00" "#00AAAA"
                             "#AA0000" "#AA00AA" "#AA5500" "#AAAAAA"
                             "#555555" "#5555FF" "#55FF55" "#55FFFF"
                             "#FF5555" "#FF55FF" "#FFFF55" "#FFFFFF")
                           8 24 :title "EGA and VGA 16 colour hardware palette")
            made)
      (let ((web216 '()))
        (dolist (r '(0 51 102 153 204 255))
          (dolist (g '(0 51 102 153 204 255))
            (dolist (b '(0 51 102 153 204 255))
              (push (format nil "#~2,'0X~2,'0X~2,'0X" r g b) web216))))
        (push (emit-swatches "palette-web216" (nreverse web216) 18 8
                             :title "web safe 216 colour palette") made))
      (dolist (p (reverse made)) (format t "~A~%" p)))))
