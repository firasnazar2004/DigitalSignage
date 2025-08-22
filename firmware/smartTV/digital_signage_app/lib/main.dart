import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:video_player/video_player.dart';
import 'package:intl/intl.dart';

// New class to hold persistent playlist data
class PlaylistManager {
  static List<MediaItem> playlist = [];
  static int currentIndex = 0;
  static bool isPlaylistLoaded = false;
}

// New class to hold media data
class MediaItem {
  final String url;
  final String mediaType;

  MediaItem({required this.url, required this.mediaType});
}

void main() {
  runApp(DigitalSignageApp());
}

class DigitalSignageApp extends StatelessWidget {
  const DigitalSignageApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Digital Signage',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: const Color(0xFF0A0E1A),
        fontFamily: 'Roboto',
      ),
      home: HomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  _HomePageState createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> with TickerProviderStateMixin {
  String _currentTime = "";
  String _currentDate = "";
  String _temperature = "22°C"; // Mock temperature - you can integrate with weather API
  Timer? _timer;
  late AnimationController _glowController;
  late AnimationController _particleController;
  late Animation<double> _glowAnimation;

  @override
  void initState() {
    super.initState();
    _updateTime();
    _timer = Timer.periodic(Duration(seconds: 1), (timer) {
      _updateTime();
    });

    // Initialize animations
    _glowController = AnimationController(
      duration: Duration(seconds: 3),
      vsync: this,
    )..repeat(reverse: true);

    _particleController = AnimationController(
      duration: Duration(seconds: 20),
      vsync: this,
    )..repeat();

    _glowAnimation = Tween<double>(
      begin: 0.3,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _glowController,
      curve: Curves.easeInOut,
    ));
  }

  void _updateTime() {
    final now = DateTime.now();
    final timeFormatter = DateFormat('HH:mm:ss');
    final dateFormatter = DateFormat('EEEE, MMMM d, yyyy');
    setState(() {
      _currentTime = timeFormatter.format(now);
      _currentDate = dateFormatter.format(now);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _glowController.dispose();
    _particleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Animated gradient background
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFF0A0E1A),
                  Color(0xFF1A1E2E),
                  Color(0xFF16213E),
                  Color(0xFF0F172A),
                ],
                stops: [0.0, 0.3, 0.7, 1.0],
              ),
            ),
          ),

          // Animated particles
          CustomPaint(
            painter: ParticlePainter(_particleController),
            size: Size.infinite,
          ),

          // Main content
          Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Weather and date section
                Container(
                  margin: EdgeInsets.only(bottom: 40),
                  padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.2),
                      width: 1,
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.3),
                        blurRadius: 20,
                        offset: Offset(0, 10),
                      ),
                    ],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.thermostat,
                        color: Colors.cyan,
                        size: 24,
                      ),
                      SizedBox(width: 10),
                      Text(
                        _temperature,
                        style: TextStyle(
                          fontSize: 20,
                          color: Colors.white,
                          fontWeight: FontWeight.w300,
                        ),
                      ),
                      SizedBox(width: 30),
                      Icon(
                        Icons.calendar_today,
                        color: Colors.cyan,
                        size: 24,
                      ),
                      SizedBox(width: 10),
                      Text(
                        _currentDate,
                        style: TextStyle(
                          fontSize: 20,
                          color: Colors.white,
                          fontWeight: FontWeight.w300,
                        ),
                      ),
                    ],
                  ),
                ),

                // Time display with glow effect
                AnimatedBuilder(
                  animation: _glowAnimation,
                  builder: (context, child) {
                    return Container(
                      padding: EdgeInsets.symmetric(horizontal: 40, vertical: 20),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(30),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.cyan.withOpacity(_glowAnimation.value * 0.5),
                            blurRadius: 30 * _glowAnimation.value,
                            spreadRadius: 10 * _glowAnimation.value,
                          ),
                        ],
                      ),
                      child: Text(
                        _currentTime,
                        style: TextStyle(
                          fontSize: 72,
                          color: Colors.white,
                          fontWeight: FontWeight.w100,
                          letterSpacing: 4,
                          shadows: [
                            Shadow(
                              color: Colors.cyan.withOpacity(_glowAnimation.value),
                              blurRadius: 20,
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),

                SizedBox(height: 80),

                // Futuristic start button
                GestureDetector(
                  onTap: () {
                    Navigator.push(
                      context,
                      PageRouteBuilder(
                        pageBuilder: (context, animation, secondaryAnimation) => SignageDisplay(),
                        transitionsBuilder: (context, animation, secondaryAnimation, child) {
                          return FadeTransition(opacity: animation, child: child);
                        },
                        transitionDuration: Duration(milliseconds: 800),
                      ),
                    );
                  },
                  child: AnimatedBuilder(
                    animation: _glowController,
                    builder: (context, child) {
                      return Container(
                        padding: EdgeInsets.symmetric(horizontal: 50, vertical: 20),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              Color(0xFF00D4FF),
                              Color(0xFF0099CC),
                            ],
                          ),
                          borderRadius: BorderRadius.circular(50),
                          boxShadow: [
                            BoxShadow(
                              color: Color(0xFF00D4FF).withOpacity(0.4),
                              blurRadius: 20,
                              spreadRadius: 2,
                            ),
                            BoxShadow(
                              color: Color(0xFF00D4FF).withOpacity(_glowAnimation.value * 0.3),
                              blurRadius: 40,
                              spreadRadius: 5,
                            ),
                          ],
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.play_circle_filled,
                              color: Colors.white,
                              size: 28,
                            ),
                            SizedBox(width: 15),
                            Text(
                              'START PLAYLIST',
                              style: TextStyle(
                                fontSize: 18,
                                color: Colors.white,
                                fontWeight: FontWeight.w600,
                                letterSpacing: 2,
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ParticlePainter extends CustomPainter {
  final AnimationController controller;
  final List<Particle> particles = [];

  ParticlePainter(this.controller) : super(repaint: controller) {
    // Generate particles
    for (int i = 0; i < 50; i++) {
      particles.add(Particle());
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint();
    
    for (var particle in particles) {
      final progress = (controller.value + particle.offset) % 1.0;
      final x = particle.x * size.width;
      final y = (particle.y + progress * 0.1) % 1.0 * size.height;
      
      paint.color = Colors.cyan.withOpacity(
        (math.sin(progress * math.pi * 2) * 0.3 + 0.1) * particle.opacity
      );
      
      canvas.drawCircle(Offset(x, y), particle.size, paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}

class Particle {
  final double x = math.Random().nextDouble();
  final double y = math.Random().nextDouble();
  final double size = math.Random().nextDouble() * 2 + 0.5;
  final double opacity = math.Random().nextDouble() * 0.6 + 0.2;
  final double offset = math.Random().nextDouble();
}

class SignageDisplay extends StatefulWidget {
  const SignageDisplay({Key? key}) : super(key: key);

  @override
  _SignageDisplayState createState() => _SignageDisplayState();
}

class _SignageDisplayState extends State<SignageDisplay> with TickerProviderStateMixin {
  // Configuration
  static const String DISPLAY_UUID = "fa0c54d1-ba73-4797-95f6-9596d2ec5079";
  static const String API_KEY = "649418f4-1a93-4a0b-875d-50c905846d1f";
  static const String BACKEND_BASE_URL = "http://192.168.100.159:8000";
  static const int POLL_INTERVAL_SECONDS = 5;
  static const int IMAGE_DISPLAY_DURATION_SECONDS = 5;

  // State variables
  Timer? _pollTimer;
  VideoPlayerController? _videoController;
  Timer? _imageTimer;
  Timer? _mediaRotationTimer;

  // UI state variables
  bool _isInputDetected = false;
  Timer? _inputTimer;
  bool _isLoading = false;
  bool _showThumbnails = false;

  // Animation controllers
  late AnimationController _thumbnailController;
  late AnimationController _exitButtonController;
  late Animation<double> _thumbnailAnimation;
  late Animation<double> _exitButtonAnimation;

  @override
  void initState() {
    super.initState();
    _initializeAnimations();
    _initializeApp();
  }

  void _initializeAnimations() {
    _thumbnailController = AnimationController(
      duration: Duration(milliseconds: 500),
      vsync: this,
    );

    _exitButtonController = AnimationController(
      duration: Duration(milliseconds: 300),
      vsync: this,
    );

    _thumbnailAnimation = CurvedAnimation(
      parent: _thumbnailController,
      curve: Curves.easeInOut,
    );

    _exitButtonAnimation = CurvedAnimation(
      parent: _exitButtonController,
      curve: Curves.easeInOut,
    );
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    _imageTimer?.cancel();
    _mediaRotationTimer?.cancel();
    _videoController?.dispose();
    _inputTimer?.cancel();
    _thumbnailController.dispose();
    _exitButtonController.dispose();
    super.dispose();
  }

  void _handleInput() {
    if (PlaylistManager.playlist.isNotEmpty) {
      setState(() {
        _isInputDetected = true;
        _showThumbnails = !_showThumbnails;
      });

      if (_showThumbnails) {
        _thumbnailController.forward();
      } else {
        _thumbnailController.reverse();
      }

      _exitButtonController.forward();

      _inputTimer?.cancel();
      _inputTimer = Timer(Duration(seconds: 5), () {
        if (mounted) {
          setState(() {
            _isInputDetected = false;
            _showThumbnails = false;
          });
          _thumbnailController.reverse();
          _exitButtonController.reverse();
        }
      });
    }
  }

Future<void> _initializeApp() async {
    try {
      // Always start the polling mechanism to check for new media.
      _startPolling();
    } catch (e) {
      print("Initialization error: ${e.toString()}");
    }
  }

void _startPolling() {
    _pollTimer?.cancel(); // Cancel any existing timer to prevent duplicates
    _pollTimer = Timer.periodic(Duration(seconds: POLL_INTERVAL_SECONDS), (timer) {
      _synchronizeMedia();
    });
    // Call it immediately once to avoid waiting for the first interval.
    _synchronizeMedia();
  }
Future<void> _synchronizeMedia() async {
    try {
      final response = await http.get(
        Uri.parse('$BACKEND_BASE_URL/displays/$DISPLAY_UUID/sync'),
        headers: {'X-API-KEY': API_KEY},
      ).timeout(Duration(seconds: 10));

      if (response.statusCode == 200) {
        final Map<String, dynamic> responseBody = json.decode(response.body);
        final syncData = responseBody['sync_data'];
        final List<dynamic> newMedia = syncData['new_media'];
        final bool shouldOverride = syncData['override_playlist'] ?? false; // Check for override flag

        if (newMedia.isNotEmpty) {
          final newMediaItems = newMedia
              .map((item) => MediaItem(
                  url: '$BACKEND_BASE_URL/media/${item['id']}',
                  mediaType: item['type']))
              .toList();

          if (shouldOverride) {
            // If the override flag is true, clear the existing playlist.
            print("Override detected. Clearing existing playlist.");
            PlaylistManager.playlist.clear();
          }

          PlaylistManager.playlist.addAll(newMediaItems);
          PlaylistManager.isPlaylistLoaded = true;

          final List<String> newMediaIds = newMedia.map<String>((item) => item['id']).toList();
          await _markMediaAsDownloaded(newMediaIds);

          // Restart the playlist from the beginning to show the new media immediately.
          PlaylistManager.currentIndex = 0;
          _startMediaRotation();
        } else {
          // If no new media, but a playlist is already loaded, just start rotation.
          if (PlaylistManager.isPlaylistLoaded) {
            _startMediaRotation();
          } else {
            // If the playlist is not loaded yet, wait and try again.
            print("No new media found on backend. Waiting for a new upload.");
            _pollTimer = Timer(Duration(seconds: POLL_INTERVAL_SECONDS), _synchronizeMedia);
          }
        }
      } else {
        print("Sync error: status code ${response.statusCode}");
      }
    } catch (e) {
      print("Sync error: ${e.toString()}");
    }
  }
  Future<void> _markMediaAsDownloaded(List<String> mediaIds) async {
    try {
      await http.post(
        Uri.parse('$BACKEND_BASE_URL/displays/$DISPLAY_UUID/mark_downloaded_bulk'),
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': API_KEY,
        },
        body: json.encode({'media_ids': mediaIds}),
      );
    } catch (e) {
      print("Failed to mark media as downloaded: $e");
    }
  }

  void _startMediaRotation() {
    _mediaRotationTimer?.cancel();
    _showNextMedia();
  }

  Future<void> _showNextMedia() async {
    if (PlaylistManager.playlist.isEmpty) {
      _mediaRotationTimer = Timer(Duration(seconds: 3), _showNextMedia);
      return;
    }

    setState(() {
      _isLoading = true;
    });

    final currentMedia = PlaylistManager.playlist[PlaylistManager.currentIndex];

    _imageTimer?.cancel();
    if (_videoController != null) {
      await _videoController!.dispose();
      _videoController = null;
    }

    if (currentMedia.mediaType == 'video') {
      await _playVideo(currentMedia.url);
    } else {
      _showImage();
    }
  }

  Future<void> _playVideo(String videoUrl) async {
    try {
      _videoController = VideoPlayerController.networkUrl(Uri.parse(videoUrl));
      await _videoController!.initialize();
      _videoController!.play();

      setState(() {
        _isLoading = false;
      });

      _videoController!.addListener(() {
        if (_videoController!.value.position >= _videoController!.value.duration) {
          _nextMediaItem();
        }
      });
    } catch (e) {
      print('Error playing video: $e');
      setState(() {
        _isLoading = false;
      });
      _nextMediaItem();
    }
  }

  void _showImage() {
    setState(() {
      _isLoading = false;
    });

    _imageTimer = Timer(Duration(seconds: IMAGE_DISPLAY_DURATION_SECONDS), () {
      _nextMediaItem();
    });
  }

  void _nextMediaItem() {
    PlaylistManager.currentIndex = (PlaylistManager.currentIndex + 1) % PlaylistManager.playlist.length;
    _showNextMedia();
  }

  void _jumpToMedia(int index) {
    PlaylistManager.currentIndex = index;
    _showNextMedia();
    setState(() {
      _showThumbnails = false;
      _isInputDetected = false;
    });
    _thumbnailController.reverse();
    _exitButtonController.reverse();
  }

  Widget _buildMediaDisplay() {
    if (PlaylistManager.playlist.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.hourglass_empty,
              size: 64,
              color: Colors.white.withOpacity(0.7),
            ),
            SizedBox(height: 20),
            Text(
              'Loading playlist...',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 24,
                fontWeight: FontWeight.w300,
              ),
            ),
          ],
        ),
      );
    }

    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              color: Color(0xFF00D4FF),
              strokeWidth: 3,
            ),
            SizedBox(height: 20),
            Text(
              'Preparing media...',
              style: TextStyle(
                color: Colors.white.withOpacity(0.7),
                fontSize: 18,
                fontWeight: FontWeight.w300,
              ),
            ),
          ],
        ),
      );
    }

    final currentMedia = PlaylistManager.playlist[PlaylistManager.currentIndex];

    if (currentMedia.mediaType == 'video' && _videoController != null) {
      // Corrected video player rendering with a more robust check
      if (_videoController!.value.isInitialized && _videoController!.value.aspectRatio > 0) {
        return AspectRatio(
          aspectRatio: _videoController!.value.aspectRatio,
          child: VideoPlayer(_videoController!),
        );
      } else {
        // Fallback or a loading indicator while the video initializes
        return Center(
          child: CircularProgressIndicator(
            color: Color(0xFF00D4FF),
            strokeWidth: 3,
          ),
        );
      }
    } else if (currentMedia.mediaType == 'image') {
      return Image.network(
        currentMedia.url,
        fit: BoxFit.contain,
        width: double.infinity,
        height: double.infinity,
        loadingBuilder: (context, child, loadingProgress) {
          if (loadingProgress == null) return child;
          return Center(
            child: CircularProgressIndicator(
              color: Color(0xFF00D4FF),
              value: loadingProgress.expectedTotalBytes != null
                  ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
                  : null,
            ),
          );
        },
        errorBuilder: (context, error, stackTrace) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.error_outline, color: Colors.red, size: 48),
                SizedBox(height: 10),
                Text('Failed to load image', style: TextStyle(color: Colors.white, fontSize: 18)),
              ],
            ),
          );
        },
      );
    } else {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, color: Colors.red, size: 48),
            SizedBox(height: 10),
            Text('Failed to load media', style: TextStyle(color: Colors.white, fontSize: 18)),
          ],
        ),
      );
    }
  }

  Widget _buildThumbnailStrip() {
    if (PlaylistManager.playlist.isEmpty) return SizedBox.shrink();

    return AnimatedBuilder(
      animation: _thumbnailAnimation,
      builder: (context, child) {
        return Positioned(
          bottom: 20 + (100 * (1 - _thumbnailAnimation.value)),
          left: 20,
          right: 20,
          child: Opacity(
            opacity: _thumbnailAnimation.value,
            child: Container(
              height: 100,
              padding: EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.8),
                borderRadius: BorderRadius.circular(15),
                border: Border.all(
                  color: Color(0xFF00D4FF).withOpacity(0.5),
                  width: 1,
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.5),
                    blurRadius: 20,
                    offset: Offset(0, 10),
                  ),
                ],
              ),
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: PlaylistManager.playlist.length,
                padding: EdgeInsets.symmetric(horizontal: 10),
                itemBuilder: (context, index) {
                  final isCurrentMedia = index == PlaylistManager.currentIndex;
                  return GestureDetector(
                    onTap: () => _jumpToMedia(index),
                    child: Container(
                      width: 80,
                      margin: EdgeInsets.only(right: 10),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: isCurrentMedia 
                              ? Color(0xFF00D4FF) 
                              : Colors.white.withOpacity(0.3),
                          width: isCurrentMedia ? 3 : 1,
                        ),
                        boxShadow: isCurrentMedia ? [
                          BoxShadow(
                            color: Color(0xFF00D4FF).withOpacity(0.5),
                            blurRadius: 10,
                            spreadRadius: 2,
                          ),
                        ] : null,
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: Stack(
                          children: [
                            Container(
                              color: Colors.grey[800],
                              child: Center(
                                child: Icon(
                                  PlaylistManager.playlist[index].mediaType == 'video' 
                                      ? Icons.play_circle_fill 
                                      : Icons.image,
                                  color: Colors.white.withOpacity(0.8),
                                  size: 24,
                                ),
                              ),
                            ),
                            if (PlaylistManager.playlist[index].mediaType == 'image')
                              Image.network(
                                PlaylistManager.playlist[index].url,
                                fit: BoxFit.cover,
                                width: double.infinity,
                                height: double.infinity,
                                errorBuilder: (context, error, stackTrace) {
                                  return Container(
                                    color: Colors.grey[800],
                                    child: Icon(
                                      Icons.broken_image,
                                      color: Colors.white.withOpacity(0.5),
                                    ),
                                  );
                                },
                              ),
                            if (isCurrentMedia)
                              Container(
                                decoration: BoxDecoration(
                                  gradient: LinearGradient(
                                    begin: Alignment.topCenter,
                                    end: Alignment.bottomCenter,
                                    colors: [
                                      Colors.transparent,
                                      Color(0xFF00D4FF).withOpacity(0.3),
                                    ],
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    bool showExitButton = PlaylistManager.playlist.isEmpty || _isInputDetected;

    return Scaffold(
      backgroundColor: Colors.black,
      body: GestureDetector(
        onTap: _handleInput,
        child: Stack(
          children: [
            // Main media display
            Center(
              child: _buildMediaDisplay(),
            ),

            // Thumbnail strip
            if (_showThumbnails) _buildThumbnailStrip(),

            // Exit button
            if (showExitButton)
              AnimatedBuilder(
                animation: _exitButtonAnimation,
                builder: (context, child) {
                  return Positioned(
                    top: 20 + (50 * (1 - _exitButtonAnimation.value)),
                    left: 20,
                    child: Opacity(
                      opacity: _exitButtonAnimation.value,
                      child: GestureDetector(
                        onTap: () {
                          Navigator.pop(context);
                        },
                        child: Container(
                          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [
                                Colors.red.withOpacity(0.9),
                                Colors.red[700]!.withOpacity(0.9),
                              ],
                            ),
                            borderRadius: BorderRadius.circular(25),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.red.withOpacity(0.3),
                                blurRadius: 10,
                                spreadRadius: 2,
                              ),
                            ],
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.exit_to_app,
                                color: Colors.white,
                                size: 20,
                              ),
                              SizedBox(width: 8),
                              Text(
                                'EXIT',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.white,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: 1,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),

            // Media counter (bottom right)
            if (PlaylistManager.playlist.isNotEmpty && _isInputDetected)
              Positioned(
                bottom: 20,
                right: 20,
                child: AnimatedBuilder(
                  animation: _exitButtonAnimation,
                  builder: (context, child) {
                    return Opacity(
                      opacity: _exitButtonAnimation.value,
                      child: Container(
                        padding: EdgeInsets.symmetric(horizontal: 15, vertical: 8),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.7),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: Color(0xFF00D4FF).withOpacity(0.5),
                            width: 1,
                          ),
                        ),
                        child: Text(
                          '${PlaylistManager.currentIndex + 1} / ${PlaylistManager.playlist.length}',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}