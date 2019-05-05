import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from sklearn import model_selection
import argparse

# reconstraction is taken from https://github.com/vadim-v-lebedev/audio_style_tranfer/blob/master/audio_style_transfer.ipynb
def spectogram_to_wav(spectogram_content, dst_path, N_CHANNELS, N_FFT, fs):
    a = np.zeros_like(spectogram_content[0])
    a[:N_CHANNELS, :] = np.exp(spectogram_content[0]) - 1

    # reconstruction
    p = 2 * np.pi * np.random.random_sample(a.shape) - np.pi
    for i in range(500):
        s = a * np.exp(1j * p)
        x = librosa.istft(s)
        p = np.angle(librosa.stft(x, N_FFT))

    librosa.output.write_wav(dst_path, x, fs)


"""
Given two np.array that were read using librosa.load, combines both.
volume1, volume2 - amount (0 to 1) for wanted volume to combine
"""
def combine_two_wavs(wav1, wav2, volume1=1, volume2=1):
    combined = (wav1*volume1+wav2*volume2)/2
    return combined


# creates spectogram from array.
# returns (spectogram, N_CHANNELS)
def create_spectogram(src_audio, N_FFT):
    spectogram = librosa.stft(src_audio, N_FFT)
    spectogram_content = np.log1p(np.abs(spectogram[np.newaxis, :, :]))
    N_CHANNELS = spectogram_content.shape[1]
    return np.squeeze(spectogram_content, axis=0), N_CHANNELS


def create_train_test_spectograms(dir_list, sounds_train, rotors_train , N_FFT, phase='train'):
    sound_dir, rotors_dir, train_dir, valid_dir = dir_list
    for sound in sounds_train:
        print(f'processing {sound}')
        sound_path = os.path.join(sound_dir, sound)
        # possible augmentation
        sound_audio, fs_s = librosa.load(sound_path)
        fs = fs_s
        spectogram_sound_valid, N_CHANNELS = create_spectogram(sound_audio, N_FFT)
        for rotor in rotors_train:
            rotor_path = os.path.join(rotors_dir, rotor)
            rotor_audio, fs_r = librosa.load(rotor_path)
            if fs_s != fs_r:
                print("Error. unable to combine wavs. Don't have the same fs.")
                exit()
            combined_audio = combine_two_wavs(rotor_audio, sound_audio, volume1=0.2)
            spectogram_combined, N_CHANNELS = create_spectogram(combined_audio, N_FFT)
            # save combined rotor and sound
            dst_name = sound[:-4] + '_' + rotor[:-4] + '.jpg'
            if (phase == 'train'):
                dst_train_name = 'train_'+dst_name
                dst_valid_name = 'valid_' + dst_name
            else:
                dst_train_name = 'test_combined_' + dst_name
                dst_valid_name = 'test_sounds_' + dst_name
            dst_path = os.path.join(train_dir, dst_train_name)
            plt.imsave(dst_path, spectogram_combined)
            #print(f'combined spectogram {dst_train_name} saved.')
            # save validation sound only
            dst_path = os.path.join(valid_dir, dst_valid_name)
            plt.imsave(dst_path, spectogram_sound_valid)
            #print(f'sound spectogram {dst_valid_name} saved.')
    return fs, N_CHANNELS


"""
example of use in command line: python preprocess_audio.py -rotors_dir '...'
"""
def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rotors_dir', '-rotors_dir', help='enter rotors_dir', default='C:\\Users\\Tom\\Documents\\Learning_stuff\\semester 8\\Denoising_project\\data\\rotor')
    parser.add_argument('--sound_dir', '-sound_dir', help='enter sound_dir', default='C:\\Users\\Tom\\Documents\\Learning_stuff\\semester 8\\Denoising_project\\data\\Mic8')
    parser.add_argument('--train_dir', '-train_dir', help='enter train_dir', default='C:\\Users\\Tom\\Documents\\Learning_stuff\\semester 8\\Denoising_project\\data_spectograms\\train')
    parser.add_argument('--valid_dir', '-valid_dir', help='enter valid_dir', default='C:\\Users\\Tom\\Documents\\Learning_stuff\\semester 8\\Denoising_project\\data_spectograms\\valid')
    parser.add_argument('--test_dir_combined', '-test_dir_combined', help='enter test_dir_combined', default='C:\\Users\\Tom\\Documents\\Learning_stuff\\semester 8\\Denoising_project\\data_spectograms\\test_combined')
    parser.add_argument('--test_dir_sounds', '-test_dir_sounds', help='enter test_dir_sounds', default='C:\\Users\\Tom\\Documents\\Learning_stuff\\semester 8\\Denoising_project\\data_spectograms\\test_sounds')
    parser.set_defaults(console=False)
    args = parser.parse_args()
    return args


# init args and serial
args = parse_cli_args()

# given two folders, creates train:valid:test folders
sounds_list = [f for f in os.listdir(args.sound_dir)]
rotors_list = [f for f in os.listdir(args.rotors_dir)]
# split to train:valid:test
sounds_train, sounds_test = model_selection.train_test_split(sounds_list, train_size=0.9)
rotors_train, rotors_test = model_selection.train_test_split(rotors_list, train_size=0.9)
print(f'train sounds size: {len(sounds_train)}, train rotors size: {len(rotors_train)}')
print(f'test sounds size: {len(sounds_test)}, test rotors size: {len(rotors_test)}')

N_FFT = 1024

# create train and test spectograms
print('processing train files')
train_dirs_list = [args.sound_dir, args.rotors_dir, args.train_dir, args.valid_dir]
fs, N_CHANNELS = create_train_test_spectograms(train_dirs_list, sounds_train, rotors_train, N_FFT, phase='train')
print('processing test files')
test_dirs_list = [args.sound_dir, args.rotors_dir, args.test_dir_combined, args.test_dir_sounds]
create_train_test_spectograms(test_dirs_list, sounds_test, rotors_test, N_FFT, phase='test')
