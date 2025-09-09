/**
 * Production Webpack Configuration for WriteCrew Word Add-in
 * Optimized build configuration for enterprise deployment
 */

const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = (env, argv) => {
    const isProduction = argv.mode === 'production';
    const isAnalyze = env && env.analyze;
    
    return {
        mode: 'production',
        
        // Entry points for different components
        entry: {
            taskpane: './src/taskpane/taskpane.js',
            commands: './src/commands/commands.js',
            polyfills: './src/polyfills/polyfills.js'
        },
        
        // Output configuration
        output: {
            path: path.resolve(__dirname, 'dist'),
            filename: '[name].[contenthash:8].js',
            chunkFilename: '[name].[contenthash:8].chunk.js',
            publicPath: './',
            clean: true
        },
        
        // Optimization configuration
        optimization: {
            minimize: true,
            minimizer: [
                // JavaScript minification
                new TerserPlugin({
                    terserOptions: {
                        compress: {
                            drop_console: true,
                            drop_debugger: true,
                            pure_funcs: ['console.log', 'console.info', 'console.debug']
                        },
                        mangle: {
                            safari10: true
                        },
                        format: {
                            comments: false
                        }
                    },
                    extractComments: false
                }),
                
                // CSS minification
                new CssMinimizerPlugin({
                    minimizerOptions: {
                        preset: [
                            'default',
                            {
                                discardComments: { removeAll: true }
                            }
                        ]
                    }
                })
            ],
            
            // Code splitting configuration
            splitChunks: {
                chunks: 'all',
                cacheGroups: {
                    // Vendor libraries
                    vendor: {
                        test: /[\\/]node_modules[\\/]/,
                        name: 'vendors',
                        chunks: 'all',
                        priority: 10
                    },
                    
                    // Office.js specific
                    office: {
                        test: /[\\/]node_modules[\\/]@microsoft[\\/]office-js/,
                        name: 'office',
                        chunks: 'all',
                        priority: 20
                    },
                    
                    // Common utilities
                    common: {
                        name: 'common',
                        minChunks: 2,
                        chunks: 'all',
                        priority: 5,
                        reuseExistingChunk: true
                    }
                }
            },
            
            // Runtime chunk
            runtimeChunk: {
                name: 'runtime'
            }
        },
        
        // Module resolution
        resolve: {
            extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
            alias: {
                '@': path.resolve(__dirname, 'src'),
                '@components': path.resolve(__dirname, 'src/components'),
                '@services': path.resolve(__dirname, 'src/services'),
                '@utils': path.resolve(__dirname, 'src/utils'),
                '@assets': path.resolve(__dirname, 'assets')
            },
            fallback: {
                // Node.js polyfills for browser environment
                'buffer': require.resolve('buffer'),
                'crypto': require.resolve('crypto-browserify'),
                'stream': require.resolve('stream-browserify'),
                'util': require.resolve('util'),
                'url': require.resolve('url'),
                'querystring': require.resolve('querystring-es3')
            }
        },
        
        // Module rules
        module: {
            rules: [
                // JavaScript/TypeScript
                {
                    test: /\.(js|jsx|ts|tsx)$/,
                    exclude: /node_modules/,
                    use: [
                        {
                            loader: 'babel-loader',
                            options: {
                                presets: [
                                    ['@babel/preset-env', {
                                        targets: {
                                            browsers: ['> 1%', 'last 2 versions', 'ie >= 11']
                                        },
                                        useBuiltIns: 'entry',
                                        corejs: 3
                                    }],
                                    '@babel/preset-react',
                                    '@babel/preset-typescript'
                                ],
                                plugins: [
                                    '@babel/plugin-proposal-class-properties',
                                    '@babel/plugin-proposal-object-rest-spread',
                                    '@babel/plugin-transform-runtime'
                                ],
                                cacheDirectory: true
                            }
                        }
                    ]
                },
                
                // CSS/SCSS
                {
                    test: /\.(css|scss|sass)$/,
                    use: [
                        MiniCssExtractPlugin.loader,
                        {
                            loader: 'css-loader',
                            options: {
                                modules: {
                                    auto: true,
                                    localIdentName: '[name]__[local]--[hash:base64:5]'
                                },
                                sourceMap: false
                            }
                        },
                        {
                            loader: 'postcss-loader',
                            options: {
                                postcssOptions: {
                                    plugins: [
                                        ['autoprefixer', {
                                            overrideBrowserslist: ['> 1%', 'last 2 versions', 'ie >= 11']
                                        }],
                                        ['cssnano', {
                                            preset: 'default'
                                        }]
                                    ]
                                }
                            }
                        },
                        'sass-loader'
                    ]
                },
                
                // Images
                {
                    test: /\.(png|jpe?g|gif|svg|ico)$/i,
                    type: 'asset',
                    parser: {
                        dataUrlCondition: {
                            maxSize: 8 * 1024 // 8kb
                        }
                    },
                    generator: {
                        filename: 'images/[name].[hash:8][ext]'
                    }
                },
                
                // Fonts
                {
                    test: /\.(woff|woff2|eot|ttf|otf)$/i,
                    type: 'asset/resource',
                    generator: {
                        filename: 'fonts/[name].[hash:8][ext]'
                    }
                },
                
                // Office.js specific handling
                {
                    test: /office-js/,
                    use: 'null-loader'
                }
            ]
        },
        
        // Plugins
        plugins: [
            // Clean dist folder
            new CleanWebpackPlugin(),
            
            // Extract CSS
            new MiniCssExtractPlugin({
                filename: '[name].[contenthash:8].css',
                chunkFilename: '[name].[contenthash:8].chunk.css'
            }),
            
            // HTML generation for taskpane
            new HtmlWebpackPlugin({
                template: './src/taskpane/taskpane.html',
                filename: 'taskpane.html',
                chunks: ['runtime', 'vendors', 'office', 'common', 'taskpane'],
                inject: 'body',
                minify: {
                    removeComments: true,
                    collapseWhitespace: true,
                    removeRedundantAttributes: true,
                    useShortDoctype: true,
                    removeEmptyAttributes: true,
                    removeStyleLinkTypeAttributes: true,
                    keepClosingSlash: true,
                    minifyJS: true,
                    minifyCSS: true,
                    minifyURLs: true
                }
            }),
            
            // HTML generation for commands
            new HtmlWebpackPlugin({
                template: './src/commands/commands.html',
                filename: 'commands.html',
                chunks: ['runtime', 'vendors', 'office', 'common', 'commands'],
                inject: 'body',
                minify: {
                    removeComments: true,
                    collapseWhitespace: true,
                    removeRedundantAttributes: true,
                    useShortDoctype: true,
                    removeEmptyAttributes: true,
                    removeStyleLinkTypeAttributes: true,
                    keepClosingSlash: true,
                    minifyJS: true,
                    minifyCSS: true,
                    minifyURLs: true
                }
            }),
            
            // Copy static assets
            new CopyWebpackPlugin({
                patterns: [
                    {
                        from: 'manifest.xml',
                        to: 'manifest.xml',
                        transform(content) {
                            // Update manifest for production
                            return content.toString()
                                .replace(/localhost:3000/g, process.env.PRODUCTION_URL || 'https://writecrew.app')
                                .replace(/http:/g, 'https:');
                        }
                    },
                    {
                        from: 'assets/icons',
                        to: 'assets/icons'
                    },
                    {
                        from: 'assets/images',
                        to: 'assets/images'
                    }
                ]
            }),
            
            // Gzip compression
            new CompressionPlugin({
                algorithm: 'gzip',
                test: /\.(js|css|html|svg)$/,
                threshold: 8192,
                minRatio: 0.8
            }),
            
            // Bundle analyzer (conditional)
            ...(isAnalyze ? [
                new BundleAnalyzerPlugin({
                    analyzerMode: 'static',
                    openAnalyzer: false,
                    reportFilename: 'bundle-report.html'
                })
            ] : [])
        ],
        
        // Performance hints
        performance: {
            hints: 'warning',
            maxEntrypointSize: 512000, // 500kb
            maxAssetSize: 512000, // 500kb
            assetFilter: (assetFilename) => {
                return !assetFilename.endsWith('.map');
            }
        },
        
        // Source maps (disabled in production for security)
        devtool: false,
        
        // Stats configuration
        stats: {
            colors: true,
            modules: false,
            children: false,
            chunks: false,
            chunkModules: false
        },
        
        // External dependencies (loaded via CDN in production)
        externals: {
            // Office.js is loaded from Microsoft CDN
            'office-js': 'Office'
        }
    };
};

