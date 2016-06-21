const autoprefixer = require('autoprefixer');
const csso = require('postcss-csso');
const gulp = require('gulp');
const postcss = require('gulp-postcss');
const sass = require('gulp-sass');

// Server

gulp.task('default', ['styles'], () => {
	gulp.watch('bc_pipelines/base/static_src/css/**/*.scss', ['styles']);
});

// Styles

gulp.task('styles', () => {
	return gulp.src('bc_pipelines/base/static_src/css/site.scss')
		.pipe(sass().on('error', sass.logError))
        .pipe(postcss([
			autoprefixer,
			csso
		]))
		.pipe(gulp.dest('bc_pipelines/base/static/css'));
});

